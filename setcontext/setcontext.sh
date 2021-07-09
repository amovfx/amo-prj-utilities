setcontext () {
  conda activate amo-prj-utilities;
  eval `python /Users/andrewoseen/git/amo-prj-utilities/setcontext/setcontext.py setcontext $1`;
}

delcontext () {
  #this is meant to destr
  local context=$1;
	tput setaf 1; echo Removing conda evn;
	conda remove $1;
	local project_name=$(echo $1 | sed "s/[^[:alnum:]-]//g");
	gcloud projects delete $project_name --quiet;
	rm -rf ~/git/$1;
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

del_remote_repo () {
  local git_user=$(git config user.name)
  local access_token=$(cat /Users/andrewoseen/git/amo-prj-utilities/setcontext/delete_repo_token)
  echo "$access_token"
  local git_repos=$(curl "https://api.github.com/users/$git_user/repos?per_page=100" | grep -o 'git@[^"]*')
  #curl -u amovfx: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 -X "DELETE" https://api.github.com/repos/amovfx/test
  for repo in $git_repos
  do
    echo $repo
  done

}


