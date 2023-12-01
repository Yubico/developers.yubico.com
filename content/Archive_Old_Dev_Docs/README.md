# Old documentation

This folder contains documentation that has been removed or moved from dev.yubico.com to docs.yubico.com.

These docs have been preserved here in case a customer requests an old manual or doc site contributors need to reference past material.

The docs in this folder are organized by product. The content files represent the most recent state of the content prior to removal.

## Removed books

The following table lists documentation that have been replaced/moved from dev.yubico.com to docs.yubico.com and preserved in this folder.

| Book Title | Book Slug | books.yaml Filepath | old-docs filepath | Old URL | Redirect | Reason for Removal | Removal Date |
|------------|-----------|---------------------|-------------------|---------|----------|--------------------|--------------|
| YubiHSM2 | YubiHSM2 | content/YubiHMS2 | developers.yubico.com/content/YubiHMS2 | https://developers.yubico.com/YubiHSM2/ | https://docs.yubico.com/hardware/yubihsm-2/hsm-2-user-guide/index.html | Content absorbed into combined YubiHSM 2 User Guide | 9/25/2023 |


## View an old book's PDF output

To view an old book's PDF output, open the folder containing the book of interest, then go to **pdf-output** -> **webdocs.pdf**. HTML output is not preserved due to the number of files involved and resulting increase in the size of the repository.

## Building an old book locally

If you would like to build the docs locally (HTML and/or PDF previews), do so just as you would for current books (e.g. ``make autobuild_web``). All of the book's files and folders (config file, Makefile, index file, etc) are included.

However, if the doc system is updated in the future, those updates may require changes to books' config files, Makefiles, folder structures, etc. Old books may not be updated to comply with such changes, which may result in errors when trying to build the docs with the current toolset.

Some of the files are in asciidoc (.adoc) format, the make autobuild steps for building HTML or PDF do not apply. 
