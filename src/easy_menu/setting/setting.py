from __future__ import division, print_function, absolute_import, unicode_literals

import os
import locale
import re
import yaml
import six
from six.moves.urllib.request import urlopen

from easy_menu.setting import arg_parser
from easy_menu.exceptions import SettingError, ConfigError
from easy_menu.util import CaseClass, cmd_util, string_util

DEFAULT_CONFIG_NAME = os.environ.get('EASY_MENU_CONFIG', 'easy-menu.yml')
URL_PATTERN = re.compile(r'^http[s]?://')


class Setting(CaseClass):
    """
    Manages all settings.
    """

    def __init__(self, config_path=None, work_dir=None, root_menu=None, encoding=None, lang=None, cache=None):
        is_url = self._is_url(config_path)
        super(Setting, self).__init__(
            ('config_path', config_path),
            ('work_dir', self._search_work_dir(work_dir, config_path, is_url)),
            ('root_menu', {} if root_menu is None else root_menu),
            ('encoding', encoding),
            ('lang', self._find_lang(lang)),
            ('cache', {} if cache is None else cache)
        )

    def copy(self, **args):
        return Setting(
            config_path=args.get('config_path', self.config_path),
            work_dir=args.get('work_dir', self.work_dir),
            root_menu=args.get('root_menu', self.root_menu),
            encoding=args.get('encoding', self.encoding),
            lang=args.get('lang', self.lang),
            cache=args.get('cache', self.cache),
        )

    @staticmethod
    def _find_lang(lang):
        if not lang:
            # environment LANG is the first priority
            lang = os.environ.get('LANG')
        if not lang:
            lang = locale.getdefaultlocale()[0]
        return lang

    @staticmethod
    def _is_url(path):
        return path is not None and bool(URL_PATTERN.match(path))

    @staticmethod
    def _search_work_dir(work_dir, config_path, is_url):
        if work_dir is None:
            if config_path is not None:
                if not is_url:
                    return os.path.dirname(config_path)
        return work_dir

    def parse_args(self, argv):
        option, args = arg_parser.parser.parse_args(argv[1:])
        path = None

        if not args:
            pass
        elif len(args) == 1:
            path = args[0]
            if not self._is_url(path):
                path = os.path.abspath(path)
        else:
            arg_parser.parser.print_help()
            arg_parser.parser.exit(2)

        return self.copy(config_path=path, work_dir=option.work_dir, encoding=option.encoding, lang=option.lang)

    def lookup_config(self):
        if self.config_path is None:
            d = os.path.abspath(self.work_dir) if self.work_dir else os.getcwd()

            while True:
                path = os.path.join(d, DEFAULT_CONFIG_NAME)
                if os.path.exists(path):
                    return self.copy(config_path=path)
                nd = os.path.dirname(d)
                if d == nd:
                    break
                d = nd
        return self

    def _load_data(self, is_command, path_or_url_or_cmdline):
        """
        Load data from one file, url or command line, then store to a dict.

        :param is_command: True if using command line output
        :param path_or_url_or_cmdline:
        :return: dict representation of data
        """

        if path_or_url_or_cmdline is None:
            raise SettingError('Not found configuration file.')

        # normalize file path
        is_url = self._is_url(path_or_url_or_cmdline)
        if not is_command and not is_url:
            if self.work_dir is not None and not os.path.isabs(path_or_url_or_cmdline):
                path_or_url_or_cmdline = os.path.join(self.work_dir, path_or_url_or_cmdline)

        # if already loaded, use cache data
        c = self.cache.get((is_command, path_or_url_or_cmdline))
        if c is not None:
            return c

        try:
            if is_command:
                # execute command
                print('Executing: %s' % path_or_url_or_cmdline)

                # ignore return code and stderr
                data = cmd_util.capture_command(path_or_url_or_cmdline, self.work_dir)[1]
            elif self._is_url(path_or_url_or_cmdline):
                # read from URL
                print('Reading from URL: %s' % path_or_url_or_cmdline)
                data = urlopen(path_or_url_or_cmdline).read()
            else:
                # read from file as bytes
                print('Reading file: %s' % path_or_url_or_cmdline)
                data = open(path_or_url_or_cmdline, 'rb').read()

            # If --encode option is not set, we use utf-8 for parsing YAML file.
            menu = yaml.load(data.decode(self.encoding if self.encoding else 'utf-8'))

            # update cache data (Note: cache property is mutable!)
            self.cache[(is_command, path_or_url_or_cmdline)] = menu
        except IOError:
            raise ConfigError(path_or_url_or_cmdline, 'Failed to open.')
        except yaml.YAMLError as e:
            raise ConfigError(path_or_url_or_cmdline, 'YAML format error: %s' % e)
        return menu

    def load_meta(self):
        root_menu = self._load_data(False, self.config_path)

        # overwrite working directory
        work_dir = root_menu.get('meta', {}).get('work_dir')
        return self.copy(work_dir=work_dir)

    def load_config(self):
        """
        Load the configuration file or url.

        If it contains 'include' sections, load them recursively.
        :return: updated Setting instance
        """

        def build_config(config, is_root, depth):
            """
            Validate and evaluate configuration recursively by using depth-first search.

            :param config: dict of the node or leaf
            :param is_root: True when the leaf is not allowed
            :param depth: indicator for the nesting level
            :return: validated dict of the node or leaf
            """
            # avoid for inclusion loops and stack overflow
            if depth >= 50:
                raise ConfigError(self.config_path, 'Nesting level too deep.')

            # config should be a dict which contains only one item except 'meta'
            if not isinstance(config, dict):
                raise ConfigError(self.config_path, 'Menu must be dict, not %s.' % type(config).__name__)

            config = dict((k, v) for k, v in config.items() if k not in ['meta'])

            if len(config) != 1:
                raise ConfigError(self.config_path, 'Menu should have only one item, not %s.' % len(config))

            name, content = list(six.iteritems(config))[0]
            t = type(content).__name__

            if name == 'include':
                # content should be a leaf
                if not isinstance(content, six.string_types):
                    raise ConfigError(self.config_path, '"include" section must have string content, not %s.' % t)

                return build_config(self._load_data(False, content), True, depth + 1)
            elif name == 'eval':
                # content should be a leaf
                if not isinstance(content, six.string_types):
                    raise ConfigError(self.config_path, '"eval" section must have string content, not %s.' % t)

                return build_config(self._load_data(True, content), True, depth + 1)
            else:
                if isinstance(content, list):
                    content = [build_config(child, False, depth + 1) for child in content]
                elif isinstance(content, six.string_types):
                    if is_root:
                        raise ConfigError(self.config_path, 'Root content must be list, not %s.' % t)
                else:
                    raise ConfigError(self.config_path, 'Content must be string or list, not %s.' % t)
            return {string_util.to_unicode(name, self.encoding): content}

        root_menu = build_config(self._load_data(False, self.config_path), True, 0)

        return self.copy(root_menu=root_menu)
