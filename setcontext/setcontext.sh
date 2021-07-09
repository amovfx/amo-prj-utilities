setcontext () {
  conda activate amo-prj-utilities;
  eval `python /Users/andrewoseen/git/amo-prj-utilities/setcontext/setcontext.py setcontext $1`;
}



removecontext () {
  #this is meant to destr
  conda activate amo-prj-utilities
  if [ $# -eq 0 ]
    then
      echo "No arguments"
      local project=$(basename "$PWD")
    else
      local project=$1
  fi
  echo "Removing context: $project"

  #set directory
  cd ~/git/

  #delete google-project
  gcloud projects delete $project

  #remove conda env
  conda env remove -n $project

  #remove remote repo
  local git_user=$(git config user.name)
  local access_token=$(cat /Users/andrewoseen/git/amo-prj-utilities/setcontext/delete_repo_token)
  echo "Removing https://api.github.com/repos/$git_user/$project"
  curl -u $git_user:$access_token -X "DELETE" https://api.github.com/repos/$git_user/$project

  #remove folder
  rm -rf ~/git/"$project"

  #clear environment variables
  eval `python /Users/andrewoseen/git/amo-prj-utilities/setcontext/setcontext.py clear_context_env_variables`;
  eval `python /Users/andrewoseen/git/amo-prj-utilities/setcontext/setcontext.py set_terminal_prompt`

}



delcontexts () {
  for d in $1; do
    delcontext $d
  done
}

del_conda_envs () {

  for i in $(conda env list --json | jq -c '.envs[]'); do
    echo "Delete $i (y/n)?";
    read CONT </dev/tty;
      if [ "$CONT" = "y" ]; then
        local env_name=$(python -c "import sys; print(sys.argv[1].split('/')[-1].strip('\"'))" $i)
        conda env remove -n $env_name
      else
        echo "Skipping";
      fi
  done

}

list_repos () {
  local git_user=$(git config user.name)
  curl "https://api.github.com/users/$git_user/repos?per_page=100" | grep -o 'git@[^"]*'
}

del_remote_repo () {
  local git_user=$(git config user.name)
  local access_token=$(cat /Users/andrewoseen/git/amo-prj-utilities/setcontext/delete_repo_token)
  echo "$access_token"
  local git_repos=$(curl "https://api.github.com/users/$git_user/repos?per_page=100" | grep -o 'git@[^"]*')
  local repo_array=($(python -c "import sys; print(' '.join(sys.argv[1].splitlines()))" $git_repos))
  for repo in $repo_array; do
    repo_name=$(echo $repo | awk -F/ '{print $2}' | awk -F. '{print $1}')
    echo "Delete $repo_name (y/n)?";
    read CONT </dev/tty;
      if [ "$CONT" = "y" ]; then
        echo Deleteing "repo_name"
        echo "-u $git_user:$access_token -X /"DELETE/" https://api.github.com/repos/$git_user/$repo_name"
        curl -u $git_user:$access_token -X "DELETE" https://api.github.com/repos/$git_user/$repo_name
      else
        echo "Skipping $repo_name"
      fi
  done
}

del_local_repo () {
  for repo in ~/git/*/; do
    echo "Delete $repo? (y/n)?"
    read CONT </dev/tty;
    if [ "$CONT" = "y" ]; then
      echo "deleting $repo"
      folder_name=$(echo $repo)
      rm -rf "$repo"
    else
      echo "Skipping..."
    fi
  done
}



