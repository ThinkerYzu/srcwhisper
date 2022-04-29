# SrcWhisper

SrcWhisper is a tool to discuss source code.

It is cumbersome to ask or tell people how a function or feature
works.  It may cross several files or a big file.  Usually, people
give file names, function names, and line numbers to explain the code
he is talking about.  However, it is not only tediously for people
writing the message but also tedious for readers switching between the
message and source files.

SrcWhisper lets you annotate source code and collect these comments to
a list.  You don't need to type file names and line numbers anymore.
Readers see the annotated line by clicking a comment.


# Requirements

 - Django
 - pygments
 - flup (if you run it as a fastcgi script)

