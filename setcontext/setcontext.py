from enum import Enum
import fire
import functools
import json
import logging
import os
import re
import pathlib
import subprocess

from termcolor import cprint

#todo Add pytest

DEBUG = True
PATH = pathlib.Path.home() / "git"


class CONTEXT(Enum):
    """

    Enum type class to remove strings from code.
    These are the essential environment variable names.

    """
    PROJECT = "PROJECT"
    SERVICE = "SERVICE"
    VERSION = "VERSION"
    ACTIVECONTEXT = "ACTIVECONTEXT"

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

class TCOLOR(Enum):
    """

    Enum for terminal colors.

    """
    RED = "31m"
    GREEN = "32m"
    YELLOW = "33m"
    BLUE = "34m"
    PURPLE = "35m"
    CYAN = "36m"
    WHITE = "0m"


def is_project_name_valid_for_gcloud(name: str) -> bool:
    """

    Tests for valid name for a gcloud project name.

    :param name:
        Project name.
    :return:
        True if name only has lower space letters, digits and a dash
    """

    patterns = '^[a-z0-9/-]*$'
    if re.search(patterns, name):
        return True
    else:
        return False

@functools.lru_cache
def does_gcloud_project_exist(project_name: str) -> bool:
    """

    Test to see if a gcloud project exists.

    :param project_name:
        Name of project.
    :return: bool
        True if a gcloud project exists with the name of project_name

    """

    output = subprocess.check_output("gcloud projects list --format json".split(" "))
    json_str = output.decode('utf-8')
    json_data = json.loads(json_str)

    project_names = [project['name'] for project in json_data]

    return True if project_name in project_names else False

def does_project_or_library_exist(project_or_library_name: str) -> bool:
    """

    Quick function to see if the project or library exists in the git folder.

    :param project_or_library_name:
        The name of the project or library
    :return: bool
        True if path exists
    """

    path = PATH / project_or_library_name
    return path.is_dir()


def does_service_version_exist(service_or_version_name: str) -> bool:
    """

    Function to test if the service or version exists. Essentially checking if a sub namespace exists.

    :param service_or_version_name:
        Name of the service or version

    :return: bool
        True if the path is an existing directory.
    """

    path = pathlib.Path.cwd()
    path /= service_or_version_name
    return path.is_dir()


def is_version_string_valid(version_string: str) -> bool:
    """

    Checks if the version string is of the right format.

    :param version_string:
        A string in the format v<XXX>
    :return:  bool
        True if version_string starts with v, and ends with 3 numbers.

    """

    match = re.match(r"v\d\d\d$", version_string)
    if not match:
        raise ValueError( "Version string format should be v<000-999>")
    else:
        return True


def split_namespace(namespace: str):
    """

    Splits the namespace string into seperate variables.

    :param namespace:
        The context namespace in the format project:service:version

    :rtype: str,str,str
        the project, service and version seperated into their own variables. If contexts weren't present in the namespace
        the strings return empty.

    """
    project = ""
    service = ""
    version = ""

    # replace with argparse for better error handling and help?
    if not ":" in namespace:
        project = namespace
        service = ""
        version = ""

    else:
        split_context = namespace.split(":")
        split_count = len(split_context)

        if split_count == 2:
            project, service = split_context
            version = ''

        if split_count == 3:
            project, service, version = split_context
            is_version_string_valid(version)

    return project, service, version


def set_context_env_variable(context_type: str, value: str) -> None:
    """

    :param context_type:
        The type of variable replaced to set context, either PROJECT, SERVICE or VERSION

    :param value:
        The value to set for the environment variable.

    """
    type_upper = context_type.upper()
    if CONTEXT.has_value(type_upper):
        print(f"echo \tExporting {value} to {type_upper} | sed 's/^/  /';")
        print(f"export {type_upper}={value};")





def pprint(msg: str, color: str = 'default', indent: int = 0) -> None:
    """

    Print's colored text to the terminal with arguments for indents

    :param msg:
        The message

    :param color:
        Termcolor.cprints colors 'red', 'green', 'blue'

    :param indent:
        The amount of tabs you want precedding your message.
    """
    cprint("\t"*indent + msg, color)


class SetContext(object):

    def change_directory_path(self,
                              project_name=None,
                              service_name=None,
                              version_name=None):
        """

        This builds the path of the project from environment variables. If no project environment variables exist,
        Then the directory defaults to ~/git

        eval `python setcontext.py build_directory_path`
        """
        path = PATH
        if project_name:
            path /= project_name

        if service_name:
            path /= service_name

        if version_name:
            path /= version_name

        # add beta or alpha flags

        path_str = path.absolute().as_posix()

        self.tprint(f"Setting current working directory to: {path_str}", TCOLOR.PURPLE, indent=2)

        if path.is_dir():
            print(f"cd {path_str};")

        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"cd {path_str};")
    #memoize

    def clear_context_env_variables(self):
        """

        Sets the context environment variables to '' to avoid shell navigation errors. If a user sets the contexts to a project
        from a lower namespace such as a service or a version, we will want the environment variables to be empty.

        """
        print("echo Clearing context environment variables...;")
        for var in ["PROJECT", "SERVICE", "VERSION"]:
            set_context_env_variable(context_type=var, value='')
        print("echo \n;")

    def set_terminal_prompt(self, project=None,
                            service=None,
                            version=None):
        """

        Outputs a string to be evaluated by bash that will set the terminal prompt based on environment variables.
        Can be run from bash: eval `python setcontext.py set_terminal_prompt`

        """
        prompt_string = "PS1="

        if project:
            prompt_string += "'%F{65}'${PROJECT}"

        if service:
            prompt_string += "'%F{default}:%F{46}'${SERVICE}"

        if version:
            prompt_string += "'%F{default}:%F{38}'${VERSION}"

        prompt_string += "'%F{default} >> ';"
        print(prompt_string)


    def create_gcloud_project(self, project_name: str) -> None:
        """

        Outputs a string to be evaluated by bash that will create a gcloud project.
        Can be run from bash: eval `python setcontext.py create_gcloud_project --project_name=<project_name>`

        :param project_name:
            The name of the project gcloud will create

        """

        print(f"gcloud components update --quiet && gcloud projects create {project_name};")
        self.set_gcloud_project(project_name)
        print("gcloud app create --region=us-central;")

    def delete_gcloud_projects(self):

        output = subprocess.check_output("gcloud projects list --format json".split(" "))
        json_str = output.decode('utf-8')
        json_data = json.loads(json_str)

        for project in json_data:
            prj_id = project['projectId']
            print(f"echo Deleting project: {prj_id};")
            print(f"gcloud projects delete {prj_id};")

    def delete_conda_envs(self):
        output = subprocess.check_output("conda env list --json".split(" "))
        json_str = output.decode('utf-8')
        json_data = json.loads(json_str)

        for env in json_data["envs"]:
            if input(f"echo Delete {env.split('/')[-1]}: ").lower() == 'y':
                print (f"echo Confirmed: deleteing {env}")
                output = subprocess.check_output(f"conda env remove -n {env.split('/')[-1]}")






    def set_gcloud_project(self, project_name: str) -> None:
        """

         Outputs a string to be evaluated by bash that will switch gcloud project.
         Can be run from bash: eval `python setcontext.py sete_gcloud_project --project_name=<project_name>`

         :param project_name:
             The name of the project gcloud project
         """

        print(f"gcloud config set project {project_name};")


    def create_conda_env(self, env_name: str) -> None:
        """

        Outputs a string to be evaluated by bash that will create a conda environment.

        :param env_name:
            The name of the conda environment, it is meant to match the project name
        """

        print(f"conda create -y -q --name {env_name} python=3.8;")

    def set_conda_env(self, env_name: str) -> None:
        """

        Outputs a string to be evaluated by bash that will set the conda environment.

        :param env_name:
        """
        self.tprint(f"Setting conda env: {env_name}", TCOLOR.BLUE, 3)
        print(f"conda activate {env_name};")

    def create_git_repo(self):
        """

        Outputs a string to be evaluated by bash that will initialize a git remo and use hub create to create a remote repo.

        """

        print("git init && hub create;")

    def print_project_variables(self):
        """
            Prints out the essential environment variables.

            python SetContext.py print_project_variables

        """

        pprint("SetContext Environment Variables: ", 'yellow')
        for member in CONTEXT:
            pprint(f"{member}: {os.environ[member]}", 'red', 1)


    def setcontext(self, namespace: str, debug: int=0):
        """

        Main program to call all the sub functions for setting context between projects.
        This generates a bash script to be called from the shell and evaluated.

        Ex:
        eval `python setcontext.py setcontext my_project_name:my_service_or_module/v<001-999>

        :param namespace:
            A string to determine where you are working. project:service:version

        """

        project, service, version = split_namespace(namespace)
        self.tprint("Setting context", "GREEN",0)
        if debug:
            print(f"echo Setting Context to namespace {project}:{service}:{version}...;")

        if project and is_project_name_valid_for_gcloud(project):
            self.clear_context_env_variables()
            set_context_env_variable(CONTEXT.PROJECT.value, project)
            self.change_directory_path(project_name=project)
            if does_gcloud_project_exist(project_name=project):
                self.tprint(f"Project {project} exists", "YELLOW", 1)
                self.set_gcloud_project(project_name=project)
                self.set_conda_env(env_name=project)

            else:
                self.tprint(f"Creating new project: {project}", "GREEN", 1)

                self.create_gcloud_project(project_name=project)
                self.create_conda_env(env_name=project)
                self.create_git_repo()

            self.set_terminal_prompt(project=project)

            if service:
                self.tprint(f"Setting service to: {service}", "GREEN", 2)
                set_context_env_variable(CONTEXT.SERVICE.value, service)
                self.change_directory_path(project_name=project,
                                           service_name=service)

                self.set_terminal_prompt(project=project,
                                         service=service)

            if version:
                self.tprint(f"Setting service to: {version}", "GREEN", 3)
                set_context_env_variable(CONTEXT.VERSION.value, version)
                self.change_directory_path(project_name=project,
                                           service_name=service,
                                           version_name=version)

                self.set_terminal_prompt(project=project,
                                         service=service,
                                         version=version)
        self.tprint(f"Setting ActiveContext to : {namespace}", TCOLOR.CYAN,0)
        set_context_env_variable(CONTEXT.ACTIVECONTEXT.value, namespace)

    def setmodule(self, namespace: str, debug: int=0):
        """

        This is the same as setcontext except that it doesnt create a gcloud project.

        Ex:
        eval `python setcontext.py setcontext my_project_name:my_service_or_module/v<001-999>

        :param namespace:
            A string to determine where you are working. project:service:version

        """

        project, service, version = split_namespace(namespace)
        self.tprint("Setting module", TCOLOR.GREEN, indent=1)
        if debug:
            print(f"echo Setting Context to namespace {project}:{service}:{version}...;")

        if project:
            self.clear_context_env_variables()
            set_context_env_variable(CONTEXT.PROJECT.value, project)
            if does_project_or_library_exist(project):
                self.change_directory_path(project_name=project)
                self.tprint(f"Library: {project} exists", TCOLOR.YELLOW, indent=2)

            else:
                self.change_directory_path(project_name=project)
                self.tprint(f"Creating library: {project}", TCOLOR.GREEN, indent=2)
                self.create_git_repo()

            self.set_terminal_prompt(project=project)

            if service:
                set_context_env_variable(CONTEXT.SERVICE.value, service)
                if does_service_version_exist(service):
                    self.tprint(f"Creating module: {service}", TCOLOR.GREEN, indent=2)
                    self.set_conda_env(env_name=service)
                else:
                    self.create_conda_env(env_name=service)

                self.change_directory_path(project_name=project,
                                           service_name=service)
                self.set_terminal_prompt(project=project,
                                         service=service)

        self.tprint(f"Setting ActiveContext to : {namespace}", TCOLOR.CYAN,0)
        set_context_env_variable(CONTEXT.ACTIVECONTEXT.value, namespace)

    def tprint(self, msg, color, indent=0):
        """

        This is a function that prints colored text to the terminal from bash evaluate statements.
        Usefull for debugging. This should monkeypatch the logging module.

        :param msg:
            Message you would like to print to terminal.
        :param color:
            The color of the message.
        :param indent:
            The number of dashes that should be prefixed to the message.
        :return:
            None
        """

        if isinstance(color, TCOLOR):
            color = color.value
        else:
            if isinstance(color, str):
                color_map = {k.name: k.value for k in TCOLOR}
                color = color_map[color]

        spaces = "----" * indent
        print(f"""echo -e "\033[1;{color}{spaces}{msg}\033[0m";""")
        print("echo \n;")



if __name__ == '__main__':

    def logging_extended(msg: str):
        logging.debug(f"echo {msg}")


    logging.debug = logging_extended
    fire.Fire(SetContext)



