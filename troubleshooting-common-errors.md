# Troubleshooting Common Errors

## `error  Did you really mean 'adoc'?  Vale.Spelling`

For example:
```
[rolfedh@fedora-desktop openshift-docs]$ vale cluster-logging-forwarding-about.adoc

 stdin.txt
 1:34  error  Did you really mean 'adoc'?  Vale.Spelling

✖ 1 error, 0 warnings and 0 suggestions in stdin.
```

This error happened because you made a mistake when you specified the file path or file name. When you specify the file correctly, the error disappears. For example:
```
[rolfedh@fedora-desktop openshift-docs]$ vale modules/cluster-logging-forwarding-about.adoc
✔ 0 errors, 0 warnings and 0 suggestions in 1 file.
```
