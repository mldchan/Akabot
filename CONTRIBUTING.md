# Contributing to Akabot

## How to contribute

### Simplest way to help (Finding bugs and suggesting features)

If you find a bug in the bot, have a feature request or a suggestion, you can open an issue in the repository. You can also use the bot's `/feedback suggest` and `/feedback bug` commands to contribute bug fixes and suggestions. These 2 commands will create an issue in the repository with the information you provided.

### Contributing code

To contribute code to the bot, you can follow these steps:

1. Fork the repository
2. Clone the repository
3. Create a new branch
4. Make your changes
5. Push your changes to your fork
6. Create a pull request

Recommended to develop on the newer branch of the bot. The branch that's default is considered "stable" and only receives bug fixes and minor improvements. The newer branch is considered to receive new features and improvements. If you contribute a bug fix, use the default branch. If you contribute a new feature, use the newer branch.

### Financial contributions

If you want to contribute to server costs and support Akatsuki2555 in her development, you can donate to her on [Ko-fi](https://ko-fi.com/akatsuki2555). This is not required but it's appreciated.

## Versioning

The versioning system works as following:

- When a new bot version is released to the public, set as the default branch and the primary bot instance is running this version, this version is considered to only receive bug fixes and minor improvements.
- The next version is another branch with an incremented version number. This branch is considered to receive new features and improvements.
- 2 older versions of the bot receive bug fixes and minor improvements as well. If you contribute a bug fix to the current branch, I'll backport it to 2 older versions.

## Things to consider when contributing

- When contributing, make sure to update LATEST.md with the updates you made. I might move them to a minor version in the file but please make sure to include them.
- Please use as meaningful commit messages as possible. They don't have to be necessarily long, but they should be descriptive.
- If you're contributing a new feature, please make sure to include a description of the feature in the pull request.
- If you're contributing a bug fix, please make sure to include a description of the bug in the pull request.
- Recommended if you mention related issues in the pull request description.
