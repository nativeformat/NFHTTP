#!/usr/bin/python
import sys
import logging

'''
The command line arguments are matched against a set of Parameters (that have
name and description). The parameters can be Targets, ActionParameters,
ValueParameters and OptionParameters.

Only one Target can be selected by the user. It specifies the set of operations
to execute when the ActionParameters are triggered.

The ActionParameters are the possible operations that a user can perform on the
selected Target. They are able to reorder themselves, and are triggered when
they are explicitly selected or implicitly needed.

The ValueParameters are parameters without the classic '--'. They can be used
to update a dict of strings when they are selected. This dict can be queried by
the Target.

The OptionParameters are parameters with the classic '--'. They can be used in
the same way than the ValueParameters. They can require zero or one arguments.
If an argument is required, the form '--name=value' must be used and the form
'--name value' (two different arguments in the argv) is not supported.

The steps of Options.parse() are:

# Process the Targets.
## Select the Targets from the list of Parameters.
## Search the Targets in the arguments.
### If there is none, continue with the default and available Targets instead.
### If there is one, select it.
### If there are more, abort.
### If it is not available, abort.
## The Target can add more parameters (plugins) to the list.

# Process the ActionParameters.
## Select the ActionParameters from the list of Parameters.
### For each of them, invoke action() to get an Action instance.
## Search the ActionParameters in the arguments.
### If there is none, continue with the default ActionParameters instead.
## For each Action, invoke set_selected(). true = it was found in the arguments
or is a selected default.
## The selected ActionParameters can add more parameters (plugins) to the list.

# Process the ValueParameters.
## Select the ValueParameters from the list of Parameters.
## Search the ValueParameters in the arguments.

# Process the OptionParameters.
## Select the OptionParameters from the list of Parameters.
## Search the OptionParameters in the arguments.

# If there are still arguments, abort.

# Prepare an instance of CommandLine. The instance of Options is not modified,
and the instance of CommandLine carries the results of the parsing.
## Create instance of CommandLine.
## Use opts of Target.default_opts().
## For every selected OptionParameter, invoke OptionParameter.update().
## For every selected ValueParameter, invoke ValueParameter.update().
## For every Action, invoke ValueParameter.update().

The steps of CommandLine.do():

# Run HelpAction and nothing else if it was selected.
# While there are still actions that are not is_done() or is_skipped():
## If action.can_do() and action.must_do(), then action.do() and
action.set_done() are invoked.
## If action.can_do() and not action.must_do(), then action.set_skipped() is
invoked.
## If no action returns true for can_do(), abort.
'''


class Parameter:
    '''
    Anything that can be used as command line argument
    '''
    def name(self):
        pass

    def description(self):
        pass


class Target(Parameter):
    '''
    A set of clean, deps, configure, compile, test methods.
    '''
    def is_available(self):
        '''
        the target can be used
        '''
        return True

    def is_default(self):
        '''
        target is used if no targets are explicitly specified
        '''
        return False

    def default_opts(self):
        '''
        default dict of options
        '''
        return {}

    def extra_parameters(self):
        '''
        if the target is selected, other parameters can be used
        '''
        return ()

    def dependency_names(self):
        '''
        names of the dependecies
        '''
        return ()

    def clean(self, line):
        pass

    def deps(self, line):
        pass

    def configure(self, line):
        pass

    def compile(self, line):
        pass

    def test(self, line):
        pass


class Action:
    '''
    Possible action that can be executed
    '''
    def __init__(self):
        self.selected = False
        self.done = False
        self.skipped = False

    def set_selected(self, selected):
        '''
        the user has specified the action explicitly
        '''
        self.selected = selected

    def is_selected(self):
        return self.selected

    def update(self, line):
        '''
        let update the opts
        '''
        pass

    def can_do(self, line):
        '''
        the action can be executed or skipped because all previous actions have
        been executed or skipped
        '''
        return True

    def must_do(self, line):
        '''
        the action must be executed because it was requested explicitly or is
        implicitly needed
        '''
        return self.is_selected()

    def do(self, line):
        '''
        execute the desired action, a call to some method of the selected
        target
        '''
        pass

    def set_done(self):
        '''
        the action has been executed
        '''
        self.done = True

    def is_done(self):
        return self.done

    def set_skipped(self):
        '''
        the action has been skipped
        '''
        self.skipped = True

    def is_skipped(self):
        return self.skipped

    def is_processed(self):
        '''
        the action has been executed or skipped
        '''
        return self.is_done() or self.is_skipped()


class ActionParameter(Parameter):
    '''
    A Parameter that represents an Action
    '''
    def is_default(self):
        '''
        action is used if no actions are explicitly specified
        '''
        return False

    def extra_parameters(self, target):
        '''
        other parameters can be used for a given target
        '''
        return ()

    def action(self):
        '''
        create the Action
        '''
        return Action()


class ValueParameter(Parameter):
    '''
    a Parameter that updates a dict of strings
    '''
    def update(self, line):
        pass


class OptionParameter(Parameter):
    '''
    a Parameter that represents a double dash option
    '''
    def require_arg(self):
        return False

    def update(self, line, arg):
        pass


class VerboseOptionParameter(OptionParameter):
    def name(self):
        return 'verbose'

    def description(self):
        return 'More output'

    def update(self, line, arg):
        if 'logger' in line.opts:
            logger = line.opts['logger']
            logger.setLevel(logging.DEBUG)


class HelpAction(Action):
    def text(self, options):
        parameters = options.parameters

        # search Targets
        (ptargets, parameters) = options._find_type(Target, *parameters)
        targets = {}
        for t in ptargets:
            targets[t.name()] = t

        # search ActionParameters
        (pactparams, parameters) = options._find_type(ActionParameter,
                                                      *parameters)
        actparams = {}
        for a in pactparams:
            actparams[a.name()] = a

        # search ValueParameters
        (pvalparams, parameters) = options._find_type(ValueParameter,
                                                      *parameters)
        valparams = {}
        for o in pvalparams:
            valparams[o.name()] = o

        # search OptionParameters
        (poptparams, parameters) = options._find_type(OptionParameter,
                                                      *parameters)
        optparams = {}
        for o in poptparams:
            optparams[o.name()] = o

        # text message
        s = ('Syntax: %s [targets...] [actions...] [params...]'
             " [options...] (in any order)\n") % options.name
        s += "Targets:\n"
        for name in sorted([target.name() for target in targets.values()
                            if target.is_available()]):
            target = targets[name]
            s += "  %-10s: %s" % (name, target.description())
            if target.is_default():
                s += ' (default)'
            s += "\n"
            for e in target.extra_parameters():
                if isinstance(e, ActionParameter):
                    actparams[e.name()] = e
                elif isinstance(e, ValueParameter):
                    valparams[e.name()] = e
                elif isinstance(e, OptionParameter):
                    optparams[e.name()] = e

        s += "Actions:\n"
        for name in sorted(actparams.keys()):
            actparam = actparams[name]
            s += "  %-10s: %s" % (name, actparam.description())
            if actparam.is_default():
                s += ' (default)'
            s += "\n"
            extras = []
            for target_name in sorted(targets.keys()):
                target = targets[target_name]
                if target.is_available():
                    extras += [target for p in target.extra_parameters()
                               if p.name() == name]
            if extras:
                e = ', '.join(sorted([e.name() for e in extras]))
                s += "               available for: %s\n" % e
            for target_name in sorted(targets.keys()):
                target = targets[target_name]
                if target.is_available():
                    extras = actparam.extra_parameters(target)
                    if extras:
                        e = ', '.join(sorted([e.name() for e in extras]))
                        s += "               for %s: %s\n" % (target_name, e)
                    for e in extras:
                        if isinstance(e, ValueParameter):
                            valparams[e.name()] = e
                        elif isinstance(e, OptionParameter):
                            optparams[e.name()] = e

        if valparams:
            s += "Params:\n"
            for name in sorted(valparams.keys()):
                value = valparams[name]
                s += "  %-10s: %s\n" % (name, value.description())

        if optparams:
            s += "Options:\n"
            for name in sorted(optparams.keys()):
                option = optparams[name]
                n = '--'+name
                if option.require_arg():
                    n += '=x'
                s += "  %-10s: %s\n" % (n, option.description())

        others = [target.name() for target in targets.values()
                  if not target.is_available()]
        if others:
            s += "Other targets:\n"
            for name in sorted(others):
                target = targets[name]
                s += "  %-10s: %s\n" % (name, target.description())

        return s

    def do(self, line):
        print self.text(line.options)


class HelpActionParameter(ActionParameter):

    def name(self):
        return 'help'

    def description(self):
        return 'Print this help'

    def action(self):
        return HelpAction()


class CleanAction(Action):
    def do(self, line):
        line.target.clean(line)


class CleanActionParameter(ActionParameter):

    def name(self):
        return 'clean'

    def description(self):
        return 'Clean the build directory'

    def action(self):
        return CleanAction()


class DepsParameter(ValueParameter):
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def description(self):
        return 'Download the dependency %s' % self.name()

    def update(self, line):
        opts = line.opts
        if 'deps' not in opts:
            opts['deps'] = {}
        opts['deps'][self.name()] = True


class DepsAction(Action):

    def is_used_by_others(self, line):
        for i in ['configure', 'compile', 'test']:
            if line.actions[i].must_do(line):
                return True
        return False

    def update(self, line):
        names = line.target.dependency_names()
        if names and ('deps' not in line.opts or self.is_used_by_others(line)):
            line.opts['deps'] = {}
            for name in names:
                line.opts['deps'][name] = True

    def must_do(self, line):
        if self.is_selected():
            return True
        return self.is_used_by_others(line)

    def can_do(self, line):
        return line.actions['clean'].is_processed()

    def do(self, line):
        line.target.deps(line)


class DepsActionParameter(ActionParameter):
    def name(self):
        return 'deps'

    def description(self):
        return 'Download the dependencies'

    def extra_parameters(self, target):
        return tuple(DepsParameter(name) for name in target.dependency_names())

    def action(self):
        return DepsAction()


class ConfigureAction(Action):
    def must_do(self, line):
        if self.is_selected():
            return True
        if line.actions['compile'].must_do(line):
            return True
        return False

    def can_do(self, line):
        return line.actions['deps'].is_processed()

    def do(self, line):
        line.target.configure(line)


class ConfigureActionParameter(ActionParameter):
    def name(self):
        return 'configure'

    def description(self):
        return 'Run the build script generator'

    def action(self):
        return ConfigureAction()


class CompileAction(Action):
    def must_do(self, line):
        if self.is_selected():
            return True
        for i in ['clean', 'test']:
            if not line.actions[i].must_do(line):
                return False
        return True

    def can_do(self, line):
        return line.actions['configure'].is_processed()

    def do(self, line):
        line.target.compile(line)


class CompileActionParameter(ActionParameter):
    def name(self):
        return 'compile'

    def description(self):
        return 'Run the generated build script'

    def is_default(self):
        return True

    def action(self):
        return CompileAction()


class TestAction(Action):
    def can_do(self, line):
        return line.actions['compile'].is_processed()

    def do(self, line):
        line.target.test(line)


class TestActionParameter(ActionParameter):
    def name(self):
        return 'test'

    def description(self):
        return 'Run the tests'

    def is_default(self):
        return True

    def action(self):
        return TestAction()


class DebugBuildType(ValueParameter):
    def name(self):
        return 'debug'

    def description(self):
        return 'Make a debug build (default)'

    def update(self, line):
        line.opts['build_type'] = 'debug'


class ReleaseBuildType(ValueParameter):
    def name(self):
        return 'release'

    def description(self):
        return 'Make a release build'

    def update(self, line):
        line.opts['build_type'] = 'release'


class DebugReleaseTarget(Target):
    def default_opts(self):
        return {'build_type': 'debug'}

    def extra_parameters(self):
        return (DebugBuildType(), ReleaseBuildType())


class Options:
    '''
    The build types, actions, dependencies and options can appear in any order.
    '''
    def __init__(self):
        # name
        self.name = ''
        # actions
        self.help = HelpActionParameter()
        self.clean = CleanActionParameter()
        self.deps = DepsActionParameter()
        self.configure = ConfigureActionParameter()
        self.compile = CompileActionParameter()
        self.test = TestActionParameter()
        # options
        self.verbose = VerboseOptionParameter()
        # parameters
        self.parameters = (self.help, self.clean, self.deps, self.configure,
                           self.compile, self.test, self.verbose)

    def parse(self, *args):
        parameters = self.parameters

        # select targets
        (ptargets, parameters) = self._find_type(Target, *parameters)
        targets = {}
        for t in ptargets:
            targets[t.name()] = t

        # search target in the args
        (target_name, args) = self._find_one_target(targets, *args)
        if not target_name:
            # get default target names
            defaults = [t.name() for t in targets.values()
                        if t.is_available() and t.is_default()]
            if not defaults:
                raise Exception('there are no default available targets')
            if len(defaults) > 1:
                raise Exception('there are more than one default available '
                                'targets')
            target_name = defaults[0]
        target = targets[target_name]
        if not target.is_available():
            raise Exception('target %s is not available' % target_name)
        parameters += target.extra_parameters()

        # search actions in the args
        (paction_params, parameters) = self._find_type(ActionParameter,
                                                       *parameters)
        action_params = {}
        actions = {}
        for a in paction_params:
            name = a.name()
            action_params[name] = a
            actions[name] = a.action()
        (action_param_names, args) = self._find_several_args(action_params,
                                                             *args)
        if not action_param_names:
            action_param_names = [name for name in action_params if
                                  action_params[name].is_default()]
        for name in actions:
            selected = name in action_param_names
            actions[name].set_selected(selected)
            if selected:
                parameters += action_params[name].extra_parameters(target)

        # search value parameters
        (pvalue_params, parameters) = self._find_type(ValueParameter,
                                                      *parameters)
        value_params = {}
        for a in pvalue_params:
            value_params[a.name()] = a
        (value_param_names, args) = self._find_several_args(value_params,
                                                            *args)

        # search option parameters
        (poption_params, parameters) = self._find_type(OptionParameter,
                                                       *parameters)
        option_params = {}
        for a in poption_params:
            option_params[a.name()] = a
        (option_param_names, args) = self._find_option_args(option_params,
                                                            *args)

        # abort on unknown arguments
        if args:
            raise Exception('unknown args: %s' % ', '.join(args))

        # create line
        opts = target.default_opts()
        line = CommandLine(self, target, actions, opts)

        # let option parameters update the opts
        for name, arg in option_param_names:
            option_params[name].update(line, arg)

        # let value parameters update the opts
        for name in value_param_names:
            value_params[name].update(line)

        # let actions update the opts
        for name in actions:
            actions[name].update(line)

        return line

    def _find_option_args(self, options, *args):
        found = ()
        others = ()
        for arg in args:
            ok = arg.startswith('--')
            if ok:
                split = arg[2:].split('=', 1)
                name = split[0]
                ok = name in options
                if ok:
                    option = options[name]
                    if option.require_arg():
                        if len(split) == 1:
                            raise Exception('option --%s requires an argument'
                                            % name)
                        found += ((name, split[1]),)
                    else:
                        if len(split) == 2:
                            raise Exception('option --%s requires no arguments'
                                            % name)
                        found += ((name, None),)
            if not ok:
                others += (arg,)
        return (found, others)

    def _find_type(self, type, *args):
        found = ()
        others = ()
        for arg in args:
            if isinstance(arg, type):
                found += (arg,)
            else:
                others += (arg,)
        return (found, others)

    def _find_several_args(self, items, *args):
        found = ()
        others = ()
        for arg in args:
            if arg in items:
                found += (arg,)
            else:
                others += (arg,)
        return (found, others)

    def _find_one_target(self, items, *args):
        (found, others) = self._find_several_args(items, *args)
        if not found:
            return None, others
        elif len(found) > 1:
            f = ', '.join(found)
            raise Exception('more than one targets specified: %s' % f)
        return (found[0], others)

    def do(self, *argv):
        try:
            self.name = argv[0]
            line = self.parse(*argv[1:])
        except Exception as e:
            print >> sys.stderr, e.message
            print >> sys.stderr, HelpAction().text(self)
            raise
        line.do()
        return line


class CommandLine:
    def __init__(self, options, target, actions, opts):
        # the original Options
        self.options = options
        # the selected Target
        self.target = target
        # map from name to all Actions
        self.actions = actions
        # a dict with values
        self.opts = opts

    def debug(self, *args):
        if 'logger' in self.opts:
            logger = self.opts['logger']
            logger.debug(*args)

    def info(self, *args):
        if 'logger' in self.opts:
            logger = self.opts['logger']
            logger.info(*args)

    def warning(self, *args):
        if 'logger' in self.opts:
            logger = self.opts['logger']
            logger.warning(*args)

    def error(self, *args):
        if 'logger' in self.opts:
            logger = self.opts['logger']
            logger.error(*args)

    def do(self):
        if 'help' in self.actions:
            action = self.actions['help']
            if action.must_do(self):
                action.do(self)
                return
        actions = self.actions.copy()
        while actions:
            length = len(actions)
            for name in actions.keys():
                action = actions[name]
                if action.can_do(self):
                    if action.must_do(self):
                        action.do(self)
                        action.set_done()
                    else:
                        action.set_skipped()
                    del actions[name]
            if len(actions) == length:
                a = ', '.join(actions)
                raise Exception('cyclic dependency in actions: %s' % a)
