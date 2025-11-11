#!/bin/bash
set -e

# 1. Push your changes to the 'staging' branch first
# 2. Once pushed, run this script: ./test/update_stage_tag.sh
# This script automates the process of moving the 'stage' tag
# to your current commit (HEAD) and pushing it to the remote
# to trigger the staging deployment workflow.

TAG_NAME="stage"
BRANCH_NAME="staging"
REMOTE_NAME="origin"

# 1. Check if we are on the correct branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$BRANCH_NAME" ]; then
    echo "Error: You are not on the '$BRANCH_NAME' branch."
    echo "Please run 'git checkout $BRANCH_NAME' and push your changes first."
    exit 1
fi

# 2. Check if the working directory is clean
if ! git diff-index --quiet HEAD --; then
    echo "Error: You have uncommitted changes."
    echo "Please commit or stash them before deploying."
    exit 1
fi

# 3. Check if local branch is in sync with the remote
# This ensures you have run 'git push' on your commits *before* tagging.
local_head=$(git rev-parse HEAD)
remote_head=$(git rev-parse ${REMOTE_NAME}/${BRANCH_NAME} 2>/dev/null) # 2>/dev/null handles new/empty branches

if [ "$local_head" != "$remote_head" ]; then
    echo "Error: Your local '$BRANCH_NAME' branch is not in sync with '${REMOTE_NAME}/${BRANCH_NAME}'."
    echo "This usually means you need to 'git push' your commits first."
    echo "Run 'git push ${REMOTE_NAME} ${BRANCH_NAME}' and try again."
    exit 1
fi

echo "Your local '$BRANCH_NAME' is in sync with remote. Proceeding to update tag."

# 4. Move the local tag to the latest commit
echo "Updating local tag '$TAG_NAME' to HEAD ($local_head)..."
git tag -f "$TAG_NAME"

# 5. Delete the old tag from the remote
echo "Deleting remote tag '$TAG_NAME' from '$REMOTE_NAME'..."
# Add error handling in case the remote tag doesn't exist (e.g., first deploy)
git push "$REMOTE_NAME" :refs/tags/"$TAG_NAME" || echo "Note: Remote tag didn't exist, which is fine."

# 6. Push the new tag to the remote
echo "Pushing new tag '$TAG_NAME' to '$REMOTE_NAME'..."
git push "$REMOTE_NAME" "$TAG_NAME"

echo ""
echo "Successfully moved '$TAG_NAME' tag."
echo "The staging build workflow should trigger shortly."
