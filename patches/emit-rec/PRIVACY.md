# Export privacy check

The exported patch and reproduction inputs were scanned for absolute workstation paths,
private application identifiers, team labels, and named assistant/model labels. No matches were found.
No private application source was read for this packaging task.

`emit-rec.diff` changes only the 12 source files in the demo, with 1,063 additions and 15 deletions.
The exported source patch carries no commit metadata. Comment labels were made descriptive;
executable code is unchanged from the six-commit demo.

The public inputs include the three small reproductions and real-blog's ingestion files.
Credentials, master keys, databases, and generated binaries are excluded.
Crystal dependency checkouts are fetched separately by public commit hash.
