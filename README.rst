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

Examples
========

Working with timetracker::

  $ tt start website working on documentation
  timetracker: INFO: Creating project "website".
  timetracker: INFO: Starting work on "website".
  $ tt
  You have been working on website (working on documentation) since 2011-09-21 18:32:32 (0:00:05.724626).
  You last worked on meta for 0:28:56.909626.
  $ tt list
  hpc
  email
  isilon
  code.seas
  meta
  lunch
  coffee
  homestuff
  website
  $ tt email
  timetracker: INFO: Stopping work on website (working on documentation) after 0:00:14.416366.
  timetracker: INFO: Starting work on "email".
  $ tt report -W
  hpc                  0:31:16.900541
  email                0:03:35.549148
  isilon               0:02:36.782161
  code.seas            0:05:25.168950
  meta                 2:39:44.715278
  lunch                0:45:00
  coffee               0:05:48.300289
  homestuff            0:05:51.317112
  website              0:00:14.416366
  $ tt
  You have been working on email since 2011-09-21 18:32:46 (0:00:15.246323).
  You last worked on website (working on documentation) for 0:00:14.416366.
  $ tt stop
  timetracker: INFO: Stopping work on email after 0:00:16.793932.
  $ tt
  You are not currently working on anything.
  You last worked on email for 0:00:16.793932.

