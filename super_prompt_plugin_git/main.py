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
GIT_REBASE = "R"
GIT_MERGE = "M"

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
    
    if os.path.exists(rebase_info_dir := os.path.join(repo.git_dir, "rebase-merge")) and os.path.exists(os.path.join(repo.git_dir, "REBASE_HEAD")):
        # Repo is under rebase conflict handling process
        with open(os.path.join(rebase_info_dir, "orig-head")) as original_head_fd:
            original_head_sha = original_head_fd.read().strip()
        with open(os.path.join(rebase_info_dir, "onto")) as onto_commit_fd:
            onto_commit_sha = onto_commit_fd.read().strip()
        rebase_branch_name = original_head_sha[:7]
        rebase_branch_to = onto_commit_sha[:7]
        show_onto_commit_id = False
        for branch in repo.branches:
            if branch.commit.hexsha == original_head_sha:
                rebase_branch_name = branch.name
            if branch.commit.hexsha == onto_commit_sha:
                rebase_branch_to = branch.name
                show_onto_commit_id = True
        return super_prompt.types.PluginResponse(
            GIT_REBASE + GIT_SYMBOL,
            f'{rebase_branch_name} onto {rebase_branch_to} ({onto_commit_sha[:7]})' if show_onto_commit_id else
            f'{rebase_branch_name} onto {onto_commit_sha[:7]}',
            None
        )

    if os.path.exists(os.path.join(repo.git_dir, "MERGE_HEAD")):
        # Repo is under merge conflict handling process
        with open(os.path.join(repo.git_dir, "MERGE_HEAD")) as merge_from_fd:
            merge_from_commit_hexsha = merge_from_fd.read().strip()
        merge_to_branch = repo.active_branch.name
        merge_from = merge_from_commit_hexsha[:7]
        for branch in repo.branches:
            if branch.commit.hexsha == merge_from_commit_hexsha:
                merge_from = f'{branch.name} ({merge_from_commit_hexsha[:7]})'

        return super_prompt.types.PluginResponse(
            GIT_MERGE + GIT_SYMBOL,
            f'{merge_from} -> {merge_to_branch}',
            None
        )
            

    if repo.head.is_detached:
        return super_prompt.types.PluginResponse(GIT_DIRTY + GIT_SYMBOL, "Unknown branch (DETACHED)", None)
    
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

