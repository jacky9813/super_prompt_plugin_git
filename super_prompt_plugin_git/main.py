import typing
import logging
import os

import git
import git.exc

import super_prompt.types

GIT_SYMBOL = "\U0001f709"
GIT_SYNCED = "\u2713 "
GIT_COMMIT_NOT_PUSHED = "\u21c5 "
GIT_DIRTY = "*"

logger = logging.getLogger("super_prompt_plugin_git")


def main(config: dict) -> typing.Optional[super_prompt.types.PluginResponse]:
    repo = None
    cursor = os.getcwd()
    while cursor:
        try:
            repo = git.Repo(cursor)
            break
        except git.exc.InvalidGitRepositoryError:
            next_cursor = os.path.abspath(os.path.join(cursor, ".."))
            if next_cursor == cursor:
                cursor = None
            else:
                cursor = next_cursor
    if repo is None:
        logger.info("No valid Git repo found")
        return
    branch_name = repo.active_branch.name

    if repo.is_dirty():
        return super_prompt.types.PluginResponse(GIT_DIRTY + GIT_SYMBOL, branch_name, None)

    remote_branch = repo.active_branch.tracking_branch()
    if remote_branch is None:
        return super_prompt.types.PluginResponse(GIT_SYMBOL, branch_name, None)
    
    return super_prompt.types.PluginResponse(
        (GIT_SYNCED if remote_branch.commit.hexsha == repo.active_branch.commit.hexsha else GIT_COMMIT_NOT_PUSHED) + GIT_SYMBOL,
        branch_name,
        None
    )

    

if __name__ == "__main__":
    print(main({}))

