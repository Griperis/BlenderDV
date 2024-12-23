// Thanks to https://github.com/actions/github-script/issues/273#issuecomment-1257245316

module.exports = async ({ github, context, artifact_url }) => {
    // Get pull requests that are open for current ref.
    const pullRequests = await github.rest.pulls.list({
        owner: context.repo.owner,
        repo: context.repo.repo,
        state: 'open',
        head: `${context.repo.owner}:${context.ref.replace('refs/heads/', '')}`
    })

    // Set issue number for following calls from context (if on pull request event) or from above variable.
    const issueNumber = context.issue.number || pullRequests.data[0].number

    // Retrieve existing bot comments for the PR
    const {data: comments} = await github.rest.issues.listComments({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: issueNumber,
    })
    const existingComment = comments.find(comment => {
        return comment.user.type === 'Bot' && comment.body.includes('Charts From')
    })

    // Prepare format of the comment - it has to be de-indented to make markdown work properly.
    const output = `
#### Charts From \`${context.sha}\`*

${artifact_url}
`;

    // If we have a comment, update it, otherwise create a new one
    if (existingComment) {
        github.rest.issues.updateComment({
            owner: context.repo.owner,
            repo: context.repo.repo,
            comment_id: existingComment.id,
            body: output
        })
    } else {
        github.rest.issues.createComment({
            issue_number: issueNumber,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: output
        })
    }
}