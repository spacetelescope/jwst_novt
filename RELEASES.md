The NOVT team performs software releases as needed. We employ the following procedure for creating
a new release:

    1. Create a new branch for changes related to the version release procedure.
    2. Update the release notes.
    3. Open, review, and merge a pull request with the release changes.
    4. Create a new tag/release on GitHub.
    5. Upload the new version of the software to PyPI.

Detailed instructions for performing a release are given below:

1. **Create a new branch for changes related to the version release procedure.**

    Make sure that your local version of the main branch is up-to-date. A new branch with the naming convention
    vx.y.z should be opened off of the main branch, where vx.y.z is the version number of the release
    (e.g. v0.4.1). This branch should be used for the changes described in the rest of this document.

2. **Update the release notes.**

    In CHANGES.rst, write a concise but detailed description of all notable changes that have
    occurred since the last release. One way to acquire this information is to scroll through 
    the commit history of the project, and look for commits in which a pull request was merged.

3. **Open, review, and merge a pull request with the release changes.**

    Once you've committed the changes from (2) in your branch, push your branch to GitHub using
    the upstream remote, open a pull request that points to the main branch. Assign reviewers. 
    Either you or the reviewer should eventually merge this pull requests.

4. **Create a new tag/release on GitHub.**

    Once the pull request into the production branch from (3) has been merged, click on the 
    releases button on the main page of the repository, then hit the "Draft a new release button". 
    The "Tag version" should be the version number of the release, the "Target" should be the main 
    branch, the "Release title" should (also) be the version number of the release, and the 
    "Description" should match that of the changelog entry in (2). Once all of that information is 
    added, hit the big green "Publish" release button.

5. **Upload the new version of the software to PyPI.**

    To upload the new tagged version of the software to PyPI from a local clone of the main
    spacetelescope repository, pull the latest changes, build the distribution, and upload via twine:

       - git checkout main
       - git pull
       - rm -rf dist
       - python -m build
       - python -m twine upload dist/*
