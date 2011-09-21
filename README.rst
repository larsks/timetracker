===========
TimeTracker
===========

This is a simple time tracking tool that logs time worked on various
projects in a SQLite database.

Commands
========

- ``start [ project [ comment ] ]``

  Start work on a project.  If you do not specify a project, start work on
  the project that you were mostly recently working on.

  Specifying ``start`` is optional as long as your project name
  doesn't conflict with an existing command.

- ``stop``

  Stop your current work.

- ``status``

  Show what you're currently working on and what you were
  last working on.

- ``list``

  List all projects.

- ``log project start_time stop_time [ comment ]``

  Explicitly log some work.

- ``cancel``

  Cancel your current work.

- ``report [ --today | --week | --month | --days <days> | --weeks <weeks> ] [ project [...] ]``

  Report work totals for all projects (or the specified project) for all
  time or for the specified period.

