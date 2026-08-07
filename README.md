# p4ai

A Claude Code plugin marketplace holding one plugin, `pt4ai`, a precision toolkit for working with a model.

## pt4ai

Precision Toolkit for AI: an operating discipline packaged so it runs rather than sitting in a file you meant to reread. Read the source before asserting it, verify a claim before stating it, and gates that report what they are not checking instead of reporting clean. It works in five layers, each acting at a different moment and catching a class of failure the others cannot: always-on rules, an on-demand precision-mode skill, write-time hooks, pre-publish gates that keep private material out of public work, and optional local standards servers the discipline points at.

Nothing about your work leaves your machine. The plugin ships with none of its checks configured, because each one encodes a judgment that is yours (where your material lives, what counts as private, your house style), so setup asks rather than assumes.

## Install

```
/plugin marketplace add durgadasji/p4ai
/plugin install pt4ai@p4ai
/pt4ai:setup
```

## Documentation

The full account lives in the plugin:

- `pt4ai/README.md`, what each layer and each check is for, and how to configure it.
- `pt4ai/PROVENANCE.md`, which standards the plugin asserts against and which files actually execute.
- `pt4ai/method/working-discipline.md`, the reasoning behind each rule and the failure that produced it.

## License

The `pt4ai` plugin is licensed under Apache-2.0; see `pt4ai/LICENSE`.
