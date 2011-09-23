#!/usr/bin/python

import os
import sys
import optparse
import logging
import time
import datetime
import textwrap

from sqlalchemy.sql.expression import *

import model

class TrackerError (Exception):
    pass

class Tracker (object):

    def __init__ (self):

        self.utcdelta = datetime.timedelta(
                seconds=time.daylight and time.altzone or time.timezone)

    def parse_args(self):
        p = optparse.OptionParser()
        p.disable_interspersed_args()
        p.add_option('-d', '--dburi',
                default=os.environ.get('TIMETRACKER_DBURI',
                    'sqlite:///%s' % os.path.join(os.environ['HOME'], '.timedb')))
        p.add_option('--debug', action='store_true')

        return p.parse_args()

    def setup_logging(self):
        logging.basicConfig(
                format='%(name)s: %(levelname)s: %(message)s',
                level=(self.opts.debug and logging.DEBUG or logging.INFO))

        self.log = logging.getLogger('timetracker')

    def main(self):
        self.opts, args = self.parse_args()
        self.setup_logging()

        self.log.debug('Initializing database.')
        model.init(self.opts.dburi)
        self.session = model.Session()

        try:
            try:
                cmd = args.pop(0)
            except IndexError:
                cmd = 'status'

            if cmd == 'start':
                self.cmd_start(args)
            elif cmd == 'stop':
                self.cmd_stop(args)
            elif cmd == 'list':
                self.cmd_list(args)
            elif cmd == 'status':
                self.cmd_status(args)
            elif cmd == 'report':
                self.cmd_report(args)
            elif cmd == 'cancel':
                self.cmd_cancel(args)
            elif cmd == 'drop':
                self.cmd_drop(args)
            elif cmd == 'log':
                self.cmd_log(args)
            elif cmd == 'help':
                self.cmd_help(args)
            else:
                self.cmd_start([cmd] + args)
        except TrackerError, detail:
            self.log.error(detail)
            sys.exit(1)

    def cmd_help(self, args):
        '''Show available commands.'''

        print 'TimeTracker (tt)'
        print 'by Lars Kellogg-Stedman'
        print
        print 'Available commands:'
        print
        for command in sorted((x for x in dir(self) if x.startswith('cmd_'))):
            cmdname = command[4:]
            doc = getattr(getattr(self, command), '__doc__')

            if doc is None:
                doc = '%s command' % cmdname

            try:
                cmdexample, cmdhelp = doc.split('\n', 1)
            except ValueError:
                cmdexample = cmdname
                cmdhelp = doc

            print cmdname, '--', cmdexample

            if cmdhelp:
                print textwrap.fill(textwrap.dedent(cmdhelp),
                        initial_indent='    ',
                        subsequent_indent='    ')

    def cmd_log(self, args):
        '''log <project> <start> <stop> [<comment>]
        Log work to a project.'''

        try:
            projname, time_start, time_stop = args[:3]
            comment = ' '.join(args[3:])
            project = self.get_project(projname)
            self.log_work(project, time_start, time_stop, comment)
        except ValueError:
            raise TrackerError('You need to specify a project, start time, and stop time.')

    def log_work(self, project, time_start, time_stop, comment):
        now = datetime.datetime.now()

        time_start = datetime.datetime.strptime(time_start, '%H:%M')
        time_stop = datetime.datetime.strptime(time_stop, '%H:%M')

        time_start = datetime.datetime.combine(
                now, time_start.time()) + self.utcdelta
        time_stop = datetime.datetime.combine(
                now, time_stop.time()) + self.utcdelta

        w = model.Work(project=project,
                time_start=time_start, time_stop=time_stop,
                comment=comment)

        if comment:
            comment = ' (%s)' % comment

        self.session.add(w)
        self.session.commit()

        self.log.info('Logged %s work to %s%s.',
                w.time_stop - w.time_start, project.name, comment)

    def cmd_drop(self, args):
        '''drop <project>
        Remove a project (and any associated work) from the database.'''

        try:
            projname = args.pop(0)
            project = self.get_project(projname, create=False)

            if project:
                self.drop_project(project)
            else:
                raise TrackerError('No project named "%s".' % projname)
        except IndexError:
            raise TrackerError('No project?')

    def cmd_start(self, args):
        '''start [ <project> [ <comment> ] ]
        Start work on a project.  If <project> is unspecified, start work
        on the project on which you most recently worked.'''

        w = self.find_open_work()
        if w:
            self.stop_work(w)

        try:
            projname = args.pop(0)
            project = self.get_project(projname)
        except IndexError:
            project = self.find_last_project()

        if project is None:
            raise TrackerError('No project?')

        self.start_work(project, args)

    def cmd_cancel(self, args):
        '''cancel
        Cancel your current work.'''
        w = self.find_open_work()
        if w:
            self.cancel_work(w)
        else:
            raise TrackerError("You're not doing anything right now!")

    def cmd_stop(self, args):
        '''stop
        Stop your current work.'''

        w = self.find_open_work()
        if w:
            self.stop_work(w)
        else:
            raise TrackerError("You're not doing anything right now!")

    def cmd_list(self, args):
        '''list
        List available projects.'''

        for project in self.session.query(model.Project).all():
            print project.name

    def parse_report_args(self, args):
        p = optparse.OptionParser(usage='tt report [options] [projects]')
        p.add_option('--days',
                help='Show work done in the past DAYS days.')
        p.add_option('--weeks',
                help='Show work done in the past WEEKS weeks.')
        p.add_option('--today', '--day', '-T', action='store_true',
                help='Show work done today.')
        p.add_option('--week', '-W', action='store_true',
                help='Show work done this week.')
        p.add_option('--month', '-M', action='store_true',
                help='Show work done this month.')

        p.add_option('--seconds', '-s', action='store_true',
                help='Display time in seconds.')
        p.add_option('--total',
                action='store_true',
                help='Calculate total time worked.')

        p.add_option('--all', '-a', action='store_true',
                help='Show all projects, even those with no work.')

        return p.parse_args(args)

    def start_of_week(self):
        '''Returns midnight of the most recent Monday
        as a datetime object.'''

        now = datetime.datetime.utcnow()
        midnight = datetime.datetime.combine(now, 
                datetime.time(0,0)) + self.utcdelta

        delta = datetime.timedelta(days=midnight.weekday())

        return midnight - delta

    def start_of_month(self):
        '''Returns midnight of the first day of the month
        as a datetime object.'''

        now = datetime.datetime.utcnow()
        midnight = datetime.datetime.combine(now, 
                datetime.time(0,0)) + self.utcdelta

        delta = datetime.timedelta(days=midnight.day - 1)

        return midnight - delta

    def cmd_report(self, args):
        '''report [ --today | --week | --month | --days <days> | --weeks <weeks> ] [ projects [...] ]
        Produce a report of time worked on various projects.
        '''

        now = datetime.datetime.utcnow()
        midnight = datetime.datetime.combine(now, 
                datetime.time(0,0)) + self.utcdelta

        opts, args = self.parse_report_args(args)
        projects = self.session.query(model.Project)
        
        if args:
            projects = projects.filter(model.Project.name.in_(args))

        if opts.days:
            since = midnight - datetime.timedelta(days=int(opts.days))
        elif opts.weeks:
            since = midnight - datetime.timedelta(days=7 * int(opts.weeks))
        elif opts.today:
            since = midnight
        elif opts.week:
            since = self.start_of_week()
        else:
            since = None

        total = datetime.timedelta()

        for project in projects:
            work = self.session.query(model.Work)\
                    .filter(model.Work.project==project)\
                    .filter(model.Work.time_stop != None)

            if since:
                work = work.filter(model.Work.time_start > since)

            acc = sum((w.time_stop - w.time_start for w in work),
                    datetime.timedelta())
            total += acc

            if not opts.all and acc == datetime.timedelta():
                continue
            
            if opts.seconds:
                acc = acc.seconds

            print '%-20s %s' % (project.name, acc)

        if opts.total:
            if opts.seconds:
                total = total.seconds
            print
            print '%-20s %s' % ('Total', total)

    def cmd_status(self, args):
        '''status
        Show what you're currently working on and what you last worked
        on.'''

        now = datetime.datetime.utcnow()

        w = self.find_open_work()
        if w:
            print 'You have been working on %s%s since %s (%s).' % (
                    w.project.name,
                    w.comment and ' (%s)' % w.comment or '',
                    w.time_start,
                    now - w.time_start)
        else:
            print 'You are not currently working on anything.'

        w = self.find_last_finished_work()
        if w:
            print 'You last worked on %s%s for %s.' % (
                    w.project.name,
                    w.comment and ' (%s)' % w.comment or '',
                    w.time_stop - w.time_start)

    def drop_project(self, project):
        self.log.info('Dropping project "%s".' % project.name)
        self.session.delete(project)
        self.session.commit()

    def start_work(self, project, args):
        self.log.info('Starting work on "%s".' % project.name)
        comment = ' '.join(args)
        w = model.Work(project=project, comment=comment)
        self.session.add(w)
        self.session.commit()

        return w

    def cancel_work(self, w):
        project = w.project
        comment = w.comment and ' (%s)' % w.comment or ''
        self.log.info('Canceling current work on %s%s.',
                project.name, comment)

        self.session.delete(w)
        self.session.commit()

    def stop_work(self, w):
        project = w.project
        comment = w.comment and ' (%s)' % w.comment or ''
        w.time_stop = datetime.datetime.utcnow()
        delta = w.time_stop - w.time_start
        self.log.info('Stopping work on %s%s after %s.',
                project.name, comment, delta)
        self.session.commit()

    def find_last_project(self):
        w = self.find_last_finished_work()

        return w and w.project or None

    def find_last_finished_work(self):
        return self.session.query(model.Work) \
                .filter(model.Work.time_stop!=None)\
                .order_by(desc(model.Work.time_start)).first()

    def find_open_work(self):
        return self.session.query(model.Work).filter(
                model.Work.time_stop==None).first()

    def get_project(self, projname, create=True):
        project = self.session.query(model.Project).filter(
                model.Project.name==projname).first()

        if project:
            return project
        elif create:
            return self.create_project(projname)
        else:
            return None

    def create_project(self, projname):
        self.log.info('Creating project "%s".' % projname)
        project = model.Project(name=projname)
        self.session.add(project)
        self.session.commit()

        return project

if __name__ == '__main__':

    t = Tracker()
    t.main()

