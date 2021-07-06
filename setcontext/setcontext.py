from enum import Enum
import fire
import functools
import json
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
    if type_upper in CONTEXT._value2member_map_:
        print(f"echo \tExporting {value} to {type_upper} | sed 's/^/  /';")
        print(f"export {type_upper}={value};")


def clear_context_env_variables():
    """

    Sets the context environment variables to '' to avoid shell navigation errors. If a user sets the contexts to a project
    from a lower namespace such as a service or a version, we will want the environment variables to be empty.

    """
    print("echo Clearing context environment variables...;")
    for var in ["PROJECT", "SERVICE", "VERSION"]:
        set_context_env_variable(context_type=var, value='')
    print("echo \n;")


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

        if path.is_dir():
            print(f"echo Setting dir to {path_str};")
            print(f"cd {path_str};")

        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"cd {path_str};")
    #memoize

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
        pprint(f"{CONTEXT.PROJECT.value}: {os.environ[CONTEXT.PROJECT.value]}", 'red', 1)
        pprint(f"{CONTEXT.SERVICE.value}: {os.environ[CONTEXT.SERVICE.value]}", 'red', 1)
        pprint(f"{CONTEXT.VERSION.value}: {os.environ[CONTEXT.VERSION.value]}", 'red', 1)

    def tprint(self, msg, color='default', indent=0):
        #todo: change this to a debug print
        print(f"echo {msg};")


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
        self.tprint("Setting context")
        if debug:
            print(f"echo Setting Context to namespace {project}:{service}:{version}...;")

        if project and is_project_name_valid_for_gcloud(project):
            clear_context_env_variables()
            set_context_env_variable(CONTEXT.PROJECT.value, project)
            self.change_directory_path(project_name=project)
            if does_gcloud_project_exist(project_name=project):
                self.tprint("Project exists | sed 's/^/  /'")
                self.set_gcloud_project(project_name=project)
                self.set_conda_env(env_name=project)

            else:
                self.tprint("Creating new project | sed 's/^/  /'")

                self.create_gcloud_project(project_name=project)
                self.create_conda_env(env_name=project)
                self.create_git_repo()

            self.set_terminal_prompt(project=project)

            if service:
                set_context_env_variable(CONTEXT.SERVICE.value, service)
                self.change_directory_path(project_name=project,
                                           service_name=service)

                self.set_terminal_prompt(project=project,
                                         service=service)

            if version:
                set_context_env_variable(CONTEXT.VERSION.value, version)
                self.change_directory_path(project_name=project,
                                           service_name=service,
                                           version_name=version)

                self.set_terminal_prompt(project=project,
                                         service=service,
                                         version=version)

if __name__ == '__main__':
    fire.Fire(SetContext)



