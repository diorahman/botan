#!/usr/bin/env python

"""
Configuration program for botan (http://botan.randombit.net/)
  (C) 2009 Jack Lloyd
  Distributed under the terms of the Botan license

Tested with
   CPython 2.4, 2.5, 2.6 - OK
   Jython 2.5 - Target detection does not work (use --os and --cpu)

   Has not been tested with IronPython or PyPy
"""

import sys
import os
import os.path
import platform
import re
import shlex
import shutil
import string
import subprocess
import logging
import getpass
import time

from optparse import (OptionParser, OptionGroup,
                      IndentedHelpFormatter, SUPPRESS_HELP)

class BuildConfigurationInformation(object):

    """
    Version information
    """
    version_major = 1
    version_minor = 8
    version_patch = 5
    version_so_patch = 5
    version_suffix = '-pre'

    version_string = '%d.%d.%d%s' % (
        version_major, version_minor, version_patch, version_suffix)
    soversion_string = '%d.%d.%d%s' % (
        version_major, version_minor, version_so_patch, version_suffix)

    """
    Constructor
    """
    def __init__(self, options, modules):
        self.build_dir = os.path.join(options.with_build_dir, 'build')

        self.checkobj_dir = os.path.join(self.build_dir, 'checks')
        self.libobj_dir = os.path.join(self.build_dir, 'lib')

        self.include_dir = os.path.join(self.build_dir, 'include')
        self.full_include_dir = os.path.join(self.include_dir, 'botan')

        all_files = sum([mod.add for mod in modules], [])

        self.headers = sorted(
            [file for file in all_files if file.endswith('.h')])

        self.sources = sorted(set(all_files) - set(self.headers))

        checks_dir = os.path.join(options.base_dir, 'checks')

        self.check_sources = sorted(
            [os.path.join(checks_dir, file) for file in os.listdir(checks_dir)
             if file.endswith('.cpp')])

    def doc_files(self):
        docs = ['readme.txt']

        for docfile in ['api.pdf', 'tutorial.pdf', 'fips140.pdf',
                        'api.tex', 'tutorial.tex', 'fips140.tex',
                        'credits.txt', 'license.txt', 'log.txt',
                        'thanks.txt', 'todo.txt', 'pgpkeys.asc']:
            filename = os.path.join('doc', docfile)
            if os.access(filename, os.R_OK):
                docs.append(filename)
        return docs

    def pkg_config_file(self):
        return 'botan-%d.%d.pc' % (self.version_major,
                                   self.version_minor)

    def username(self):
        return getpass.getuser()

    def hostname(self):
        return platform.node()

    def timestamp(self):
        return time.ctime()

"""
Handle command line options
"""
def process_command_line(args):
    parser = OptionParser(
        formatter = IndentedHelpFormatter(max_help_position = 50),
        version = BuildConfigurationInformation.version_string)

    target_group = OptionGroup(parser, 'Target options')

    target_group.add_option('--cc', dest='compiler',
                            help='set the desired build compiler')
    target_group.add_option('--os',  default=platform.system().lower(),
                            help='set the target operating system [%default]')
    target_group.add_option('--cpu',
                            help='set the target processor type/model')
    target_group.add_option('--with-endian', metavar='ORDER', default=None,
                            help='override guess of CPU byte order')

    build_group = OptionGroup(parser, 'Build options')

    build_group.add_option('--enable-shared', dest='build_shared_lib',
                           action='store_true', default=True,
                            help=SUPPRESS_HELP)
    build_group.add_option('--disable-shared', dest='build_shared_lib',
                           action='store_false',
                           help='disable building a shared library')

    build_group.add_option('--enable-asm', dest='asm_ok',
                           action='store_true', default=True,
                           help=SUPPRESS_HELP)
    build_group.add_option('--disable-asm', dest='asm_ok',
                           action='store_false',
                           help='disallow use of assembler')

    build_group.add_option('--enable-debug', dest='debug_build',
                           action='store_true', default=False,
                           help='enable debug build')
    build_group.add_option('--disable-debug', dest='debug_build',
                           action='store_false', help=SUPPRESS_HELP)

    build_group.add_option('--with-tr1-implementation', metavar='WHICH',
                           dest='with_tr1', default=None,
                           help='enable TR1 (options: none, system, boost)')

    build_group.add_option('--with-build-dir',
                           metavar='DIR', default='',
                           help='setup the build in DIR')

    build_group.add_option('--makefile-style', metavar='STYLE', default=None,
                           help='choose a makefile style (unix, nmake)')

    build_group.add_option('--with-local-config',
                           dest='local_config', metavar='FILE',
                           help='include the contents of FILE into build.h')

    build_group.add_option('--dumb-gcc', dest='dumb_gcc',
                           action='store_true', default=False,
                           help=SUPPRESS_HELP)

    mods_group = OptionGroup(parser, 'Module selection')

    mods_group.add_option('--enable-modules', dest='enabled_modules',
                          metavar='MODS', action='append', default=[],
                          help='enable specific modules')
    mods_group.add_option('--disable-modules', dest='disabled_modules',
                          metavar='MODS', action='append', default=[],
                          help='disable specific modules')

    for mod in ['openssl', 'gnump', 'bzip2', 'zlib']:

        # This is just an implementation of Optik's append_const action,
        # but that is not available in Python 2.4's optparse, so use a
        # callback instead

        def optparse_callback(option, opt, value, parser, dest, mod):
            parser.values.__dict__[dest].append(mod)

        mods_group.add_option('--with-%s' % (mod),
                              action='callback',
                              callback=optparse_callback,
                              callback_kwargs = {
                                  'dest': 'enabled_modules', 'mod': mod }
                              )

        mods_group.add_option('--without-%s' % (mod), help=SUPPRESS_HELP,
                              action='callback',
                              callback=optparse_callback,
                              callback_kwargs = {
                                  'dest': 'disabled_modules', 'mod': mod }
                              )

    install_group = OptionGroup(parser, 'Installation options')

    install_group.add_option('--prefix', metavar='DIR',
                             help='set the base install directory')
    install_group.add_option('--docdir', metavar='DIR',
                             help='set the documentation install directory')
    install_group.add_option('--libdir', metavar='DIR',
                             help='set the library install directory')
    install_group.add_option('--includedir', metavar='DIR',
                             help='set the include file install directory')

    parser.add_option_group(target_group)
    parser.add_option_group(build_group)
    parser.add_option_group(mods_group)
    parser.add_option_group(install_group)

    # These exist only for autoconf compatability (requested by zw for mtn)
    compat_with_autoconf_options = [
        'bindir',
        'datadir',
        'datarootdir',
        'dvidir',
        'exec-prefix',
        'htmldir',
        'infodir',
        'libexecdir',
        'localedir',
        'localstatedir',
        'mandir',
        'oldincludedir',
        'pdfdir',
        'psdir',
        'sbindir',
        'sharedstatedir',
        'sysconfdir'
        ]

    for opt in compat_with_autoconf_options:
        parser.add_option('--' + opt, help=SUPPRESS_HELP)

    (options, args) = parser.parse_args(args)

    if args != []:
        raise Exception('Unhandled option(s): ' + ' '.join(args))
    if options.with_endian != None and \
       options.with_endian not in ['little', 'big']:
        raise Exception('Bad value to --with-endian "%s"' % (
            options.with_endian))

    def parse_module_opts(modules):
        return sorted(set(sum([s.split(',') for s in modules], [])))

    options.enabled_modules = parse_module_opts(options.enabled_modules)
    options.disabled_modules = parse_module_opts(options.disabled_modules)

    return options

"""
Generic lexer function for info.txt and src/build-data files
"""
def lex_me_harder(infofile, to_obj, allowed_groups, name_val_pairs):

    class LexerError(Exception):
        def __init__(self, msg, line):
            self.msg = msg
            self.line = line

        def __str__(self):
            return '%s at %s:%d' % (self.msg, infofile, self.line)

    (dirname, basename) = os.path.split(infofile)

    to_obj.lives_in = dirname
    if basename == 'info.txt':
        (dummy,to_obj.basename) = os.path.split(dirname)
    else:
        to_obj.basename = basename

    lexer = shlex.shlex(open(infofile), infofile, posix=True)
    lexer.wordchars += '|:.<>/,-!' # handle various funky chars in info.txt

    for group in allowed_groups:
        to_obj.__dict__[group] = []
    for (key,val) in name_val_pairs.iteritems():
        to_obj.__dict__[key] = val

    def lexed_tokens(): # Convert to an interator
        token = lexer.get_token()
        while token != None:
            yield token
            token = lexer.get_token()

    for token in lexed_tokens():
        match = re.match('<(.*)>', token)

        # Check for a grouping
        if match is not None:
            group = match.group(1)

            if group not in allowed_groups:
                raise LexerError('Unknown group "%s"' % (group),
                                 lexer.lineno)

            end_marker = '</' + group + '>'

            token = lexer.get_token()
            while token != end_marker:
                to_obj.__dict__[group].append(token)
                token = lexer.get_token()
                if token is None:
                    raise LexerError('Group "%s" not terminated' % (group),
                                     lexer.lineno)

        elif token in name_val_pairs.keys():
            to_obj.__dict__[token] = lexer.get_token()
        else: # No match -> error
            raise LexerError('Bad token "%s"' % (token), lexer.lineno)

"""
Convert a lex'ed map (from build-data files) from a list to a dict
"""
def force_to_dict(l):
    return dict(zip(l[::3],l[2::3]))

"""
Represents the information about a particular module
"""
class ModuleInfo(object):
    def __init__(self, infofile):

        lex_me_harder(infofile, self,
                      ['add', 'requires', 'os', 'arch', 'cc', 'libs'],
                      { 'realname': '<UNKNOWN>',
                        'load_on': 'request',
                        'define': None,
                        'modset': None,
                        'uses_tr1': 'false',
                        'note': '',
                        'mp_bits': 0 })

        # Coerce to more useful types
        self.libs = force_to_dict(self.libs)

        def add_dir_name(filename):
            if filename.count(':') == 0:
                return os.path.join(self.lives_in, filename)

            # modules can request to add files of the form
            # MODULE_NAME:FILE_NAME to add a file from another module
            # For these, assume other module is always in a
            # neighboring directory; this is true for all current uses
            return os.path.join(os.path.split(self.lives_in)[0],
                                *filename.split(':'))

        self.add = map(add_dir_name, self.add)

        self.mp_bits = int(self.mp_bits)

        if self.uses_tr1 == 'yes':
            self.uses_tr1 = True
        else:
            self.uses_tr1 = False

    def __cmp__(self, other):
        if self.basename < other.basename:
            return -1
        if self.basename == other.basename:
            return 0
        return 1

class ArchInfo(object):
    def __init__(self, infofile):
        lex_me_harder(infofile, self,
                      ['aliases', 'submodels', 'submodel_aliases'],
                      { 'realname': '<UNKNOWN>',
                        'default_submodel': None,
                        'endian': None,
                        'unaligned': 'no'
                        })

        self.submodel_aliases = force_to_dict(self.submodel_aliases)

        if self.unaligned == 'ok':
            self.unaligned_ok = 1
        else:
            self.unaligned_ok = 0

    def all_submodels(self):
        return sorted(zip(self.submodels, self.submodels) +
                          self.submodel_aliases.items(),
                      key = lambda k: len(k[0]), reverse = True)

    def defines(self, target_submodel, with_endian):
        macros = ['TARGET_ARCH_IS_%s' % (self.basename.upper())]

        if self.basename != target_submodel:
            macros.append('TARGET_CPU_IS_%s' % (target_submodel.upper()))

        if with_endian:
            macros.append('TARGET_CPU_IS_%s_ENDIAN' % (with_endian.upper()))
        elif self.endian != None:
            macros.append('TARGET_CPU_IS_%s_ENDIAN' % (self.endian.upper()))

        macros.append('TARGET_UNALIGNED_LOADSTORE_OK %d' % (self.unaligned_ok))

        return macros

class CompilerInfo(object):
    def __init__(self, infofile):
        lex_me_harder(infofile, self,
                      ['so_link_flags', 'mach_opt', 'mach_abi_linking'],
                      { 'realname': '<UNKNOWN>',
                        'binary_name': None,
                        'compile_option': '-c ',
                        'output_to_option': '-o ',
                        'add_include_dir_option': '-I',
                        'add_lib_dir_option': '-L',
                        'add_lib_option': '-l',
                        'lib_opt_flags': '',
                        'check_opt_flags': '',
                        'debug_flags': '',
                        'no_debug_flags': '',
                        'shared_flags': '',
                        'lang_flags': '',
                        'warning_flags': '',
                        'dll_import_flags': '',
                        'dll_export_flags': '',
                        'ar_command': None,
                        'makefile_style': '',
                        'compiler_has_tr1': False,
                        })

        self.so_link_flags = force_to_dict(self.so_link_flags)
        self.mach_abi_linking = force_to_dict(self.mach_abi_linking)

        self.mach_opt_flags = {}

        while self.mach_opt != []:
            proc = self.mach_opt.pop(0)
            if self.mach_opt.pop(0) != '->':
                raise Exception('Parsing err in %s mach_opt' % (self.basename))

            flags = self.mach_opt.pop(0)
            regex = ''

            if len(self.mach_opt) > 0 and \
               (len(self.mach_opt) == 1 or self.mach_opt[1] != '->'):
                regex = self.mach_opt.pop(0)

            self.mach_opt_flags[proc] = (flags,regex)

        del self.mach_opt

    def mach_abi_link_flags(self, osname, arch, submodel):

        abi_link = set()
        for what in ['all', osname, arch, submodel]:
            if self.mach_abi_linking.get(what) != None:
                abi_link.add(self.mach_abi_linking.get(what))

        if len(abi_link) == 0:
            return ''
        return ' ' + ' '.join(abi_link)

    def mach_opts(self, arch, submodel):

        def submodel_fixup(tup):
            return tup[0].replace('SUBMODEL', submodel.replace(tup[1], ''))

        if submodel == arch:
            return ''

        if submodel in self.mach_opt_flags:
            return submodel_fixup(self.mach_opt_flags[submodel])
        if arch in self.mach_opt_flags:
            return submodel_fixup(self.mach_opt_flags[arch])

        return ''

    def so_link_command_for(self, osname):
        if osname in self.so_link_flags:
            return self.so_link_flags[osname]
        return self.so_link_flags['default']

    def defines(self, with_tr1):
        if with_tr1:
            if with_tr1 == 'boost':
                return ['USE_BOOST_TR1']
            elif with_tr1 == 'system':
                return ['USE_STD_TR1']
        elif self.compiler_has_tr1:
            return ['USE_STD_TR1']

        return []

class OsInfo(object):
    def __init__(self, infofile):
        lex_me_harder(infofile, self,
                      ['aliases', 'target_features', 'supports_shared'],
                      { 'realname': '<UNKNOWN>',
                        'os_type': None,
                        'obj_suffix': 'o',
                        'so_suffix': 'so',
                        'static_suffix': 'a',
                        'ar_command': 'ar crs',
                        'ar_needs_ranlib': False,
                        'install_root': '/usr/local',
                        'header_dir': 'include',
                        'lib_dir': 'lib',
                        'doc_dir': 'share/doc',
                        'install_cmd_data': 'install -m 644',
                        'install_cmd_exec': 'install -m 755'
                        })

        self.ar_needs_ranlib = bool(self.ar_needs_ranlib)

    def ranlib_command(self):
        if self.ar_needs_ranlib:
            return 'ranlib'
        else:
            return 'true' # no-op

    def defines(self):
        return ['TARGET_OS_IS_%s' % (self.basename.upper())] + \
               ['TARGET_OS_HAS_' + feat.upper()
                for feat in self.target_features]

def canon_processor(archinfo, proc):
    for ainfo in archinfo.values():
        if ainfo.basename == proc or proc in ainfo.aliases:
            return (ainfo.basename, ainfo.basename)
        else:
            for (match,submodel) in ainfo.all_submodels():
                if re.search(match, proc) != None:
                    return (ainfo.basename, submodel)

    raise Exception('Unknown or unidentifiable processor "%s"' % (proc))

def guess_processor(archinfo):
    base_proc = platform.machine()

    if base_proc == '':
        raise Exception('Could not determine target CPU; set with --cpu')

    full_proc = platform.processor().lower().replace(' ', '')
    for junk in ['(tm)', '(r)']:
        full_proc = full_proc.replace(junk, '')

    if full_proc == '':
        full_proc = base_proc

    for ainfo in archinfo.values():
        if ainfo.basename == base_proc or base_proc in ainfo.aliases:
            for (match,submodel) in ainfo.all_submodels():
                if re.search(match, full_proc) != None:
                    return (ainfo.basename, submodel)

            return canon_processor(archinfo, ainfo.basename)

    # No matches, so just use the base proc type
    return canon_processor(archinfo, base_proc)

"""
Read a whole file into memory as a string
"""
def slurp_file(filename):
    if filename is None:
        return ''
    return ''.join(open(filename).readlines())

"""
Perform template substitution
"""
def process_template(template_file, variables):
    class PercentSignTemplate(string.Template):
        delimiter = '%'

    try:
        template = PercentSignTemplate(slurp_file(template_file))
        return template.substitute(variables)
    except KeyError, e:
        raise Exception('Unbound var %s in template %s' % (e, template_file))

"""
Create the template variables needed to process the makefile, build.h, etc
"""
def create_template_vars(build_config, options, modules, cc, arch, osinfo):
    def make_cpp_macros(macros):
        return '\n'.join(['#define BOTAN_' + macro for macro in macros])

    """
    Figure out what external libraries are needed based on selected modules
    """
    def link_to():
        libs = set()
        for module in modules:
            for (osname,link_to) in module.libs.iteritems():
                if osname == 'all' or osname == osinfo.basename:
                    libs.add(link_to)
                else:
                    match = re.match('^all!(.*)', osname)
                    if match is not None:
                        exceptions = match.group(1).split(',')
                        if osinfo.basename not in exceptions:
                            libs.add(link_to)
        return sorted(libs)

    def objectfile_list(sources, obj_dir):
        for src in sources:
            basename = os.path.basename(src)

            for src_suffix in ['.cpp', '.S']:
                basename = basename.replace(src_suffix,
                                            '.' + osinfo.obj_suffix)

            yield os.path.join(obj_dir, basename)


    def choose_mp_bits():
        mp_bits = [mod.mp_bits for mod in modules if mod.mp_bits != 0]

        if mp_bits == []:
            return 32 # default

        # Check that settings are consistent across modules
        for mp_bit in mp_bits[1:]:
            if mp_bit != mp_bits[0]:
                raise Exception('Incompatible mp_bits settings found')

        return mp_bits[0]

    """
    Form snippets of makefile for building each source file
    """
    def build_commands(sources, obj_dir, flags):
        for (obj_file,src) in zip(objectfile_list(sources, obj_dir), sources):
            yield '%s: %s\n\t$(CXX) %s%s $(%s_FLAGS) %s$? %s$@\n' % (
                obj_file, src,
                cc.add_include_dir_option,
                build_config.include_dir,
                flags,
                cc.compile_option,
                cc.output_to_option)

    def makefile_list(items):
        items = list(items) # force evaluation so we can slice it
        return (' '*16).join([item + ' \\\n' for item in items[:-1]] +
                             [items[-1]])

    def prefix_with_build_dir(path):
        if options.with_build_dir != None:
            return os.path.join(options.with_build_dir, path)
        return path

    return {
        'version_major': build_config.version_major,
        'version_minor': build_config.version_minor,
        'version_patch': build_config.version_patch,
        'version':       build_config.version_string,
        'so_version': build_config.soversion_string,

        'timestamp': build_config.timestamp(),
        'user':      build_config.username(),
        'hostname':  build_config.hostname(),
        'command_line': ' '.join(sys.argv),
        'local_config': slurp_file(options.local_config),
        'makefile_style': options.makefile_style or cc.makefile_style,

        'makefile_path': prefix_with_build_dir('Makefile'),

        'prefix': options.prefix or osinfo.install_root,
        'libdir': options.libdir or osinfo.lib_dir,
        'includedir': options.includedir or osinfo.header_dir,
        'docdir': options.docdir or osinfo.doc_dir,

        'doc_src_dir': 'doc',
        'build_dir': build_config.build_dir,

        'os': options.os,
        'arch': options.arch,
        'submodel': options.cpu,

        'mp_bits': choose_mp_bits(),

        'cc': cc.binary_name + cc.mach_abi_link_flags(options.os,
                                                      options.arch,
                                                      options.cpu),

        'lib_opt': cc.lib_opt_flags,
        'mach_opt': cc.mach_opts(options.arch, options.cpu),
        'check_opt': cc.check_opt_flags,
        'lang_flags': cc.lang_flags + options.extra_flags,
        'warn_flags': cc.warning_flags,
        'shared_flags': cc.shared_flags,
        'dll_export_flags': cc.dll_export_flags,

        'so_link': cc.so_link_command_for(osinfo.basename),

        'link_to': ' '.join([cc.add_lib_option + lib for lib in link_to()]),

        'module_defines': make_cpp_macros(
            sorted(['HAS_' + m.define for m in modules if m.define])),

        'target_os_defines': make_cpp_macros(osinfo.defines()),

        'target_compiler_defines': make_cpp_macros(
            cc.defines(options.with_tr1)),

        'target_cpu_defines': make_cpp_macros(
            arch.defines(options.cpu, options.with_endian)),

        'include_files': makefile_list(build_config.headers),

        'lib_objs': makefile_list(
            objectfile_list(build_config.sources,
                            build_config.libobj_dir)),

        'check_objs': makefile_list(
            objectfile_list(build_config.check_sources,
                            build_config.checkobj_dir)),

        'lib_build_cmds': '\n'.join(
            build_commands(build_config.sources,
                           build_config.libobj_dir, 'LIB')),

        'check_build_cmds': '\n'.join(
            build_commands(build_config.check_sources,
                           build_config.checkobj_dir, 'CHECK')),

        'ar_command': cc.ar_command or osinfo.ar_command,
        'ranlib_command': osinfo.ranlib_command(),
        'install_cmd_exec': osinfo.install_cmd_exec,
        'install_cmd_data': osinfo.install_cmd_data,

        'check_prefix': prefix_with_build_dir(''),
        'lib_prefix': prefix_with_build_dir(''),

        'static_suffix': osinfo.static_suffix,
        'so_suffix': osinfo.so_suffix,

        'botan_config': prefix_with_build_dir('botan-config'),
        'botan_pkgconfig': prefix_with_build_dir(
            build_config.pkg_config_file()),

        'doc_files': makefile_list(build_config.doc_files()),

        'mod_list': '\n'.join(['%s (%s)' % (m.basename, m.realname)
                               for m in sorted(modules)]),
        }

"""
Determine which modules to load based on options, target, etc
"""
def choose_modules_to_use(options, modules):
    def enable_module(module, for_dep = False):
        # First check options for --enable-modules/--disable-modules

        if module.basename in options.disabled_modules:
            return (False, [])

        # If it was specifically requested, skip most tests (trust the user)
        if module.basename not in options.enabled_modules:
            if module.cc != [] and options.compiler not in module.cc:
                return (False, [])

            if module.os != [] and options.os not in module.os:
                return (False, [])

            if module.arch != [] and options.arch not in module.arch \
                   and options.cpu not in module.arch:
                return (False, [])

            if module.load_on == 'dep' and not for_dep:
                return (False, [])
            elif module.load_on == 'request':
                return (False, [])
            elif module.load_on == 'asm_ok' and not options.asm_ok:
                return (False, [])

        # TR1 checks
        if module.uses_tr1:
            if options.with_tr1 != 'boost' and options.with_tr1 != 'system':
                return (False, [])

        # dependency checks
        deps = []
        deps_met = True
        for req in module.requires:
            for mod in req.split('|'):
                (can_enable, deps_of_dep) = enable_module(modules[mod], True)
                if can_enable:
                    deps.append(mod)
                    deps += deps_of_dep
                    break
            else:
                deps_met = False

        if deps_met:
            return (True,deps)
        else:
            return (False, [])

    use_module = {}
    for (name,module) in modules.iteritems():
        if use_module.get(name, False) is False:
            (should_use,deps) = enable_module(module)

            use_module[name] = should_use

            if should_use:
                for dep in deps:
                    use_module[dep] = True

    return [modules[name]
            for (name,useme) in use_module.items()
            if useme]

"""
Load the info files about modules, targets, etc
"""
def load_info_files(options):

    def find_files_named(desired_name, in_path):
        for (dirpath, dirnames, filenames) in os.walk(in_path):
            if desired_name in filenames:
                yield os.path.join(dirpath, desired_name)

    modules = dict([(mod.basename, mod) for mod in
                    [ModuleInfo(info) for info in
                     find_files_named('info.txt', options.src_dir)]])

    def list_files_in_build_data(subdir):
        for (dirpath, dirnames, filenames) in \
                os.walk(os.path.join(options.build_data, subdir)):
            for filename in filenames:
                yield os.path.join(dirpath, filename)

    archinfo = dict([(os.path.basename(info), ArchInfo(info))
                     for info in list_files_in_build_data('arch')])

    osinfo   = dict([(os.path.basename(info), OsInfo(info))
                      for info in list_files_in_build_data('os')])

    ccinfo = dict([(os.path.basename(info), CompilerInfo(info))
                    for info in list_files_in_build_data('cc')])

    del osinfo['defaults'] # FIXME (remove the file)

    return (modules, archinfo, ccinfo, osinfo)

"""
Perform the filesystem operations needed to setup the build
"""
def setup_build(build_config, options, template_vars):

    """
    Copy or link the file, depending on what the platform offers
    """
    def portable_symlink(filename, target_dir):
        if 'symlink' in os.__dict__:
            def count_dirs(dir, accum = 0):
                if dir == '' or dir == os.path.curdir:
                    return accum
                (dir,basename) = os.path.split(dir)
                return accum + 1 + count_dirs(dir)

            dirs_up = count_dirs(target_dir)

            source = os.path.join(os.path.join(*[os.path.pardir]*dirs_up),
                                  filename)

            target = os.path.join(target_dir, os.path.basename(filename))

            os.symlink(source, target)

        elif 'link' in os.__dict__:
            os.link(filename,
                    os.path.join(target_dir, os.path.basename(filename)))

        else:
            shutil.copy(filename, target_dir)

    def choose_makefile_template(style):
        if style == 'nmake':
            return 'nmake.in'
        elif style == 'unix':
            if options.build_shared_lib:
                return 'unix_shr.in'
            else:
                return 'unix.in'
        else:
            raise Exception('Unknown makefile style "%s"' % (style))

    # First delete the build tree, if existing
    try:
        shutil.rmtree(build_config.build_dir)
    except OSError, e:
        logging.debug('Error while removing build dir: %s' % (e))

    for dirs in [build_config.checkobj_dir,
                 build_config.libobj_dir,
                 build_config.full_include_dir]:
        os.makedirs(dirs)

    makefile_template = os.path.join(
        options.makefile_dir,
        choose_makefile_template(template_vars['makefile_style']))

    logging.debug('Using makefile template %s' % (makefile_template))

    templates_to_proc = {
        makefile_template: template_vars['makefile_path']
        }

    for (template, sink) in [('buildh.in', 'build.h'),
                             ('botan-config.in', 'botan-config'),
                             ('botan.pc.in', build_config.pkg_config_file()),
                             ('botan.doxy.in', 'botan.doxy')]:
        templates_to_proc[os.path.join(options.build_data, template)] = \
             os.path.join(build_config.build_dir, sink)

    for (template, sink) in templates_to_proc.items():
        try:
            f = open(sink, 'w')
            f.write(process_template(template, template_vars))
        finally:
            f.close()

    logging.debug('Linking %d header files in %s' % (
        len(build_config.headers), build_config.full_include_dir))

    for header_file in build_config.headers:
        portable_symlink(header_file, build_config.full_include_dir)

def main(argv = None):
    if argv is None:
        argv = sys.argv

    logging.basicConfig(stream = sys.stdout, format = '%(message)s',
                        level = logging.INFO)

    logging.debug('%s invoked with options "%s"' % (
        argv[0], ' '.join(argv[1:])))

    logging.debug('Platform: OS="%s" machine="%s" proc="%s"' % (
        platform.system(), platform.machine(), platform.processor()))

    options = process_command_line(argv[1:])

    if options.os == "java":
        raise Exception("Jython detected: need --os and --cpu to set target")

    options.base_dir = os.path.dirname(argv[0])
    options.src_dir = os.path.join(options.base_dir, 'src')

    options.build_data = os.path.join(options.src_dir, 'build-data')
    options.makefile_dir = os.path.join(options.build_data, 'makefile')

    (modules, archinfo, ccinfo, osinfo) = load_info_files(options)

    if options.compiler is None:
        if platform.system().lower() == 'windows':
            options.compiler = 'msvc'
        else:
            options.compiler = 'gcc'
        logging.info('Guessing to use compiler %s' % (options.compiler))

    if options.compiler not in ccinfo:
        raise Exception('Unknown compiler "%s"; available options: %s' % (
            options.compiler, ' '.join(sorted(ccinfo.keys()))))

    if options.os not in osinfo:

        def find_canonical_os_name(os):
            for (name, info) in osinfo.items():
                if os in info.aliases:
                    return name
            return os # not found

        options.os = find_canonical_os_name(options.os)

        if options.os not in osinfo:
            raise Exception('Unknown OS "%s"; available options: %s' % (
                options.os, ' '.join(sorted(osinfo.keys()))))

    if options.cpu is None:
        (options.arch, options.cpu) = guess_processor(archinfo)
        logging.info('Guessing target processor is a %s/%s' % (
            options.arch, options.cpu))
    else:
        (options.arch, options.cpu) = canon_processor(archinfo, options.cpu)
        logging.debug('Canonicalizized --cpu to %s/%s' % (
            options.arch, options.cpu))

    logging.info('Target is %s-%s-%s-%s' % (
        options.compiler, options.os, options.arch, options.cpu))

    # Kind of a hack...
    options.extra_flags = ''
    if options.compiler == 'gcc':

        def is_64bit_arch(arch):
            if arch == 'alpha' or arch.endswith('64'):
                return True
            return False

        if not is_64bit_arch(options.arch) and not options.dumb_gcc:
            gcc_version = ''.join(
                subprocess.Popen(['g++', '-v'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE).communicate())

            if re.search('(4\.[01234]\.)|(3\.[34]\.)|(2\.95\.[0-4])',
                         gcc_version):
                options.dumb_gcc = True

        if options.dumb_gcc is True:
            logging.info('Setting -fpermissive to work around gcc bug')
            options.extra_flags = ' -fpermissive'

    if options.with_tr1 == None:
        if ccinfo[options.compiler].compiler_has_tr1:
            options.with_tr1 = 'system'
        else:
            options.with_tr1 = 'none'

    modules_to_use = choose_modules_to_use(options, modules)

    build_config = BuildConfigurationInformation(options, modules_to_use)
    build_config.headers.append(
        os.path.join(build_config.build_dir, 'build.h'))

    template_vars = create_template_vars(build_config, options,
                                         modules_to_use,
                                         ccinfo[options.compiler],
                                         archinfo[options.arch],
                                         osinfo[options.os])

    # Performs the I/O
    setup_build(build_config, options, template_vars)

    logging.info('Botan %s build setup is complete' % (
        build_config.version_string))

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        print >>sys.stderr, e
        #import traceback
        #traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
