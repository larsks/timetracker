#!/usr/bin/python

import os
import sys
import optparse
import logging
import datetime

from sqlalchemy.sql.expression import *

import model

class TrackerError (Exception):
    pass

class Tracker (object):

    def parse_args(self):
        p = optparse.OptionParser()
        p.disable_interspersed_args()
        p.add_option('-d', '--dburi',
                default=os.environ.get('TIMETRACKER_DBURI',
                    os.path.join(os.environ['HOME'], '.timedb')))
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
            else:
                raise TrackerError('Unsupported command: %s' % cmd)
        except TrackerError, detail:
            self.log.error(detail)
            sys.exit(1)

    def cmd_start(self, args):
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

    def cmd_stop(self, args):
        w = self.find_open_work()
        if w:
            self.stop_work(w)
        else:
            raise TrackerError("You're not doing anything right now!")

    def cmd_list(self, args):
        for project in self.session.query(model.Project).all():
            print project.name

    def parse_report_args(self, args):
        p = optparse.OptionParser()
        p.add_option('--since')
        p.add_option('--days', '-d')
        p.add_option('--week', action='store_true')
        p.add_option('--month', action='store_true')
        p.add_option('--verbose', '-v', action='store_true')

        return p.parse_args(args)

    def cmd_report(self, args):
        now = datetime.datetime.utcnow()

        opts, args = self.parse_report_args(args)
        
        if args:
            projects = self.session.query(model.Project)\
                    .filter(model.Project.name.in_(args))
        else:
            projects = self.session.query(model.Project).all()

        for p in projects:
            work = datetime.timedelta()
            
            for x in (w.time_stop - w.time_start for w in self.session.query(model.Work)\
                    .filter(model.Work.time_stop != None).filter(model.Work.project == p)):
                work += x

            print '%-20s %s' % (p.name, work)

    def cmd_status(self, args):
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

    def start_work(self, project, args):
        self.log.info('Starting work on "%s".' % project.name)
        comment = ' '.join(args)
        w = model.Work(project=project, comment=comment)
        self.session.add(w)
        self.session.commit()

        return w

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

    def get_project(self, projname):
        project = self.session.query(model.Project).filter(
                model.Project.name==projname).first()

        return project and project or self.create_project(projname)

    def create_project(self, projname):
        self.log.info('Creating project "%s".' % projname)
        project = model.Project(name=projname)
        self.session.add(project)
        self.session.commit()

        return project

if __name__ == '__main__':

    t = Tracker()
    t.main()

