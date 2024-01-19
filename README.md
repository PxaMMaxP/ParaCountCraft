# ParaCountCraft

This Pandoc plugin allows you to add margin numbers to documents.

In the filter file you can set which metadata key (YAML Frontmatter) should be used to signal that marginal numbers should be set in the current document: `metadata_key = "letter.settings.rz"`.
You can access nested metadata with a dot.

In addition, you must add the following in a suitable place in your latex template:

```latex
$if(ParaCountCraft-Preamble)$
$ParaCountCraft-Preamble$
$endif$
```

At this point, the corresponding packages are loaded and further settings are made.
