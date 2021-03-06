# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import, unicode_literals

import sys
import os
from datetime import datetime, timedelta
from mog_commons.unittest import TestCase, base_unittest, FakeInput
from mog_commons.terminal import TerminalHandler
from easy_menu.view import Terminal
from easy_menu.controller import CommandExecutor
from easy_menu.entity import Menu, Command, CommandLine, Meta
from easy_menu.exceptions import SettingError, EncodingError

from tests.easy_menu.logger.mock_logger import MockLogger
from tests.easy_menu.controller.mock_executor import MockExecutor


class TestTerminal(TestCase):
    handler = TerminalHandler(keep_input_clean=False)

    def get_exec(self, encoding='utf-8', stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, pid_dir='/tmp'):
        return CommandExecutor(MockLogger(), encoding, stdin, stdout, stderr, pid_dir)

    def test_init(self):
        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler)
        self.assertEqual(t.root_menu, {'': []})
        self.assertEqual(t.host, 'host')
        self.assertEqual(t.user, 'user')

    def test_init_error(self):
        self.assertRaises(SettingError, Terminal, {'': []}, 'host', 'user', self.get_exec(), self.handler, 0)
        self.assertRaises(SettingError, Terminal, {'': []}, 'host', 'user', self.get_exec(), self.handler, 39)
        self.assertRaises(SettingError, Terminal, {'': []}, 'host', 'user', self.get_exec(), self.handler, -1)
        self.assertRaises(SettingError, Terminal, {'': []}, 'host', 'user', self.get_exec(), self.handler, page_size=0)
        self.assertRaises(SettingError, Terminal, {'': []}, 'host', 'user', self.get_exec(), self.handler, page_size=-1)
        self.assertRaises(SettingError, Terminal, {'': []}, 'host', 'user', self.get_exec(), self.handler, page_size=10)

    def test_print_error(self):
        t = Terminal({'': []}, 'hose', 'user', self.get_exec(), handler=self.handler, encoding='ascii', lang='ja')

        with self.withAssertOutput('', '') as (out, err):
            self.assertRaisesRegexp(
                EncodingError,
                '^Failed to print menu: lang=ja, encoding=ascii$',
                lambda: t._print('\n'.join(t._get_header('Header')))
            )

    def test_get_breadcrumb(self):
        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler, encoding='utf-8', lang='C',
                     width=80)
        self.assertEqual(t._get_breadcrumb(['a' * 50, 'b' * 50]),
                         '~aaaaaaaaaaaaaaaaaaaaaa > bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb')
        self.assertEqual(t._get_breadcrumb(['a' * 75]),
                         'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        self.assertEqual(t._get_breadcrumb(['a' * 76]),
                         '~aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        self.assertEqual(t._get_breadcrumb([''] * 26),
                         ' >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  > ')
        self.assertEqual(t._get_breadcrumb([''] * 27),
                         '~ >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  >  > ')
        self.assertEqual(t._get_breadcrumb(['a' + 'あ' * 37]),
                         'aあああああああああああああああああああああああああああああああああああああ')
        self.assertEqual(t._get_breadcrumb(['あ' * 38]),
                         '~あああああああああああああああああああああああああああああああああああああ')
        self.assertEqual(t._get_breadcrumb(['a' + 'あ' * 38]),
                         '~あああああああああああああああああああああああああああああああああああああ')
        self.assertEqual(t._get_breadcrumb(['あ' * 38 + 'a']),
                         '~あああああああああああああああああああああああああああああああああああああa')

    def test_get_page(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler, encoding='utf-8', lang='C',
                     width=80)
        self.assertEqual(t.get_page(['title'], [], 0, 1), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  title',
            '--------------------------------------------------------------------------------',
            '------+-------------------------------------------------------------------------',
            '  [0] | Quit',
            '================================================================================',
            'Press menu number (0-0): '
        ]))

        self.assertEqual(t.get_page(['Main Menu', 'title'], [
            Command('menu a', [CommandLine('command a', Meta())]),
            Command('menu b', [CommandLine('command b', Meta())]),
            Command('menu c', [CommandLine('command c', Meta())]),
        ], 0, 1), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  Main Menu > title',
            '--------------------------------------------------------------------------------',
            '  [1] | menu a',
            '  [2] | menu b',
            '  [3] | menu c',
            '------+-------------------------------------------------------------------------',
            '  [0] | Return to Main Menu',
            '================================================================================',
            'Press menu number (0-3): '
        ]))

        self.assertEqual(t.get_page(['title'], [
            Command('menu a', [CommandLine('command a', Meta())]),
            Command('menu b', [CommandLine('command b', Meta())]),
            Command('menu c', [CommandLine('command c', Meta())]),
            Command('menu d', [CommandLine('command d', Meta())]),
            Command('menu e', [CommandLine('command e', Meta())]),
            Command('menu f', [CommandLine('command f', Meta())]),
            Command('menu g', [CommandLine('command g', Meta())]),
            Command('menu h', [CommandLine('command h', Meta())]),
            Command('menu i', [CommandLine('command i', Meta())]),
        ], 0, 100), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  title',
            '--------------------------------------------------------------------------------',
            '                                  Page 1 / 100                            [N] =>',
            '--------------------------------------------------------------------------------',
            '  [1] | menu a',
            '  [2] | menu b',
            '  [3] | menu c',
            '  [4] | menu d',
            '  [5] | menu e',
            '  [6] | menu f',
            '  [7] | menu g',
            '  [8] | menu h',
            '  [9] | menu i',
            '------+-------------------------------------------------------------------------',
            '  [0] | Quit',
            '================================================================================',
            'Press menu number (0-9): '
        ]))

        self.assertEqual(t.get_page(['title'], [
            Command('menu a', [CommandLine('command a', Meta())]),
            Command('menu b', [CommandLine('command b', Meta())]),
            Command('menu c', [CommandLine('command c', Meta())]),
            Command('menu d', [CommandLine('command d', Meta())]),
            Command('menu e', [CommandLine('command e', Meta())]),
            Command('menu f', [CommandLine('command f', Meta())]),
            Command('menu g', [CommandLine('command g', Meta())]),
            Command('menu h', [CommandLine('command h', Meta())]),
            Command('menu i', [CommandLine('command i', Meta())]),
        ], 8, 100), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  title',
            '--------------------------------------------------------------------------------',
            '<= [P]                            Page 9 / 100                            [N] =>',
            '--------------------------------------------------------------------------------',
            '  [1] | menu a',
            '  [2] | menu b',
            '  [3] | menu c',
            '  [4] | menu d',
            '  [5] | menu e',
            '  [6] | menu f',
            '  [7] | menu g',
            '  [8] | menu h',
            '  [9] | menu i',
            '------+-------------------------------------------------------------------------',
            '  [0] | Quit',
            '================================================================================',
            'Press menu number (0-9): '
        ]))

        self.assertEqual(t.get_page(['title'], [
            Command('menu a', [CommandLine('command a', Meta())]),
        ], 99, 100), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  title',
            '--------------------------------------------------------------------------------',
            '<= [P]                           Page 100 / 100                                 ',
            '--------------------------------------------------------------------------------',
            '  [1] | menu a',
            '------+-------------------------------------------------------------------------',
            '  [0] | Quit',
            '================================================================================',
            'Press menu number (0-1): '
        ]))

        # sub menu
        self.assertEqual(t.get_page(['Main Menu', 'title'], [
            Menu('menu a', [Command('menu b', [CommandLine('command b', Meta())])], Meta()),
            Menu('menu c', [
                Command('menu c', [CommandLine('command c', Meta())]),
                Command('menu d', [CommandLine('command d', Meta())]),
            ], Meta()),
        ], 0, 1), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  Main Menu > title',
            '--------------------------------------------------------------------------------',
            '  [1] | Go to menu a',
            '  [2] | Go to menu c',
            '------+-------------------------------------------------------------------------',
            '  [0] | Return to Main Menu',
            '================================================================================',
            'Press menu number (0-2): '
        ]))

        # multiple command lines
        self.assertEqual(t.get_page(['Main Menu', 'title'], [
            Command('menu a', [CommandLine('command a', Meta())]),
            Command('menu b', [
                CommandLine('command b', Meta()),
                CommandLine('command b', Meta()),
            ]),
            Menu('menu c', [Command('menu d', [
                CommandLine('command d', Meta()),
                CommandLine('command d', Meta()),
            ])], Meta()),
        ], 0, 1), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  Main Menu > title',
            '--------------------------------------------------------------------------------',
            '  [1] | menu a',
            '  [2] | menu b',
            '  [3] | Go to menu c',
            '------+-------------------------------------------------------------------------',
            '  [0] | Return to Main Menu',
            '================================================================================',
            'Press menu number (0-3): '
        ]))

    def test_get_page_ja(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'ホスト', 'ユーザ', self.get_exec(), handler=self.handler, encoding='utf-8', lang='ja_JP',
                     width=80)
        self.assertEqual(t.get_page(['タイトル'], [], 0, 1), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  タイトル',
            '--------------------------------------------------------------------------------',
            '------+-------------------------------------------------------------------------',
            '  [0] | 終了',
            '================================================================================',
            '番号を入力してください (0-0): '
        ]))

        self.assertEqual(t.get_page(['メインメニュー', 'タイトル'], [
            Command('メニュー a', [CommandLine('コマンド a', Meta())]),
            Command('メニュー b', [CommandLine('コマンド b', Meta())]),
            Command('メニュー c', [CommandLine('コマンド c', Meta())]),
        ], 0, 1), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  メインメニュー > タイトル',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a',
            '  [2] | メニュー b',
            '  [3] | メニュー c',
            '------+-------------------------------------------------------------------------',
            '  [0] | メインメニュー に戻る',
            '================================================================================',
            '番号を入力してください (0-3): '
        ]))

        self.assertEqual(t.get_page([
            'メインメニュー', 'タイトル1', 'タイトル2', 'タイトル3', 'タイトル4',
            'タイトル5', 'タイトル6', 'タイトル7', 'タイトル8',
        ], [
            Command('メニュー a', [CommandLine('コマンド a', Meta())]),
            Command('メニュー b', [CommandLine('コマンド b', Meta())]),
            Command('メニュー c', [CommandLine('コマンド c', Meta())]),
        ], 0, 1), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  ~ル2 > タイトル3 > タイトル4 > タイトル5 > タイトル6 > タイトル7 > タイトル8',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a',
            '  [2] | メニュー b',
            '  [3] | メニュー c',
            '------+-------------------------------------------------------------------------',
            '  [0] | タイトル7 に戻る',
            '================================================================================',
            '番号を入力してください (0-3): '
        ]))

        self.assertEqual(t.get_page(['タイトル'], [
            Command('メニュー a', [CommandLine('コマンド a', Meta())]),
            Command('メニュー b', [CommandLine('コマンド b', Meta())]),
            Command('メニュー c', [CommandLine('コマンド c', Meta())]),
            Command('メニュー d', [CommandLine('コマンド d', Meta())]),
            Command('メニュー e', [CommandLine('コマンド e', Meta())]),
            Command('メニュー f', [CommandLine('コマンド f', Meta())]),
            Command('メニュー g', [CommandLine('コマンド g', Meta())]),
            Command('メニュー h', [CommandLine('コマンド h', Meta())]),
            Command('メニュー i', [CommandLine('コマンド i', Meta())]),
        ], 0, 100), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  タイトル',
            '--------------------------------------------------------------------------------',
            '                                  Page 1 / 100                            [N] =>',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a',
            '  [2] | メニュー b',
            '  [3] | メニュー c',
            '  [4] | メニュー d',
            '  [5] | メニュー e',
            '  [6] | メニュー f',
            '  [7] | メニュー g',
            '  [8] | メニュー h',
            '  [9] | メニュー i',
            '------+-------------------------------------------------------------------------',
            '  [0] | 終了',
            '================================================================================',
            '番号を入力してください (0-9): '
        ]))

        self.assertEqual(t.get_page(['タイトル'], [
            Command('メニュー a', [CommandLine('コマンド a', Meta())]),
            Command('メニュー b', [CommandLine('コマンド b', Meta())]),
            Command('メニュー c', [CommandLine('コマンド c', Meta())]),
            Command('メニュー d', [CommandLine('コマンド d', Meta())]),
            Command('メニュー e', [CommandLine('コマンド e', Meta())]),
            Command('メニュー f', [CommandLine('コマンド f', Meta())]),
            Command('メニュー g', [CommandLine('コマンド g', Meta())]),
            Command('メニュー h', [CommandLine('コマンド h', Meta())]),
            Command('メニュー i', [CommandLine('コマンド i', Meta())]),
        ], 8, 100), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  タイトル',
            '--------------------------------------------------------------------------------',
            '<= [P]                            Page 9 / 100                            [N] =>',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a',
            '  [2] | メニュー b',
            '  [3] | メニュー c',
            '  [4] | メニュー d',
            '  [5] | メニュー e',
            '  [6] | メニュー f',
            '  [7] | メニュー g',
            '  [8] | メニュー h',
            '  [9] | メニュー i',
            '------+-------------------------------------------------------------------------',
            '  [0] | 終了',
            '================================================================================',
            '番号を入力してください (0-9): '
        ]))

        self.assertEqual(t.get_page(['タイトル'], [
            Command('メニュー a', [CommandLine('コマンド a', Meta())]),
        ], 99, 100), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  タイトル',
            '--------------------------------------------------------------------------------',
            '<= [P]                           Page 100 / 100                                 ',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a',
            '------+-------------------------------------------------------------------------',
            '  [0] | 終了',
            '================================================================================',
            '番号を入力してください (0-1): '
        ]))

        # sub menu
        self.assertEqual(t.get_page(['メインメニュー', 'タイトル'], [
            Menu('メニュー a', [Command('メニュー b', [CommandLine('コマンド b', Meta())])], Meta()),
            Menu('メニュー c', [
                Command('メニュー c', [CommandLine('コマンド c', Meta())]),
                Command('メニュー d', [CommandLine('コマンド d', Meta())]),
            ], Meta()),
        ], 0, 1), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  メインメニュー > タイトル',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a へ',
            '  [2] | メニュー c へ',
            '------+-------------------------------------------------------------------------',
            '  [0] | メインメニュー に戻る',
            '================================================================================',
            '番号を入力してください (0-2): '
        ]))

        # multiple command lines
        self.assertEqual(t.get_page(['メインメニュー', 'タイトル'], [
            Command('メニュー a', [CommandLine('コマンド a', Meta())]),
            Command('メニュー b', [
                CommandLine('コマンド b', Meta()),
                CommandLine('コマンド b', Meta()),
            ]),
            Menu('メニュー c', [Command('メニュー d', [
                CommandLine('コマンド d', Meta()),
                CommandLine('コマンド d', Meta()),
            ])], Meta()),
        ], 0, 1), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  メインメニュー > タイトル',
            '--------------------------------------------------------------------------------',
            '  [1] | メニュー a',
            '  [2] | メニュー b',
            '  [3] | メニュー c へ',
            '------+-------------------------------------------------------------------------',
            '  [0] | メインメニュー に戻る',
            '================================================================================',
            '番号を入力してください (0-3): '
        ]))

    def test_get_confirm(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler, encoding='utf-8', lang='C',
                     width=80)
        self.assertEqual(t.get_confirm('description'), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  Confirmation',
            '--------------------------------------------------------------------------------',
            '  Would execute: description',
            '================================================================================',
            'Do you really want to execute? (y/n) [n]: '
        ]))

    def test_get_confirm_ja(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'ホスト', 'ユーザ', self.get_exec(), handler=self.handler, encoding='utf-8', lang='ja_JP',
                     width=80)
        self.assertEqual(t.get_confirm('メニュー 1'), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  実行確認',
            '--------------------------------------------------------------------------------',
            '  メニュー 1 を行います。',
            '================================================================================',
            'よろしいですか? (y/n) [n]: '
        ]))

    def test_get_before_execute(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler, encoding='utf-8', lang='C',
                     width=80)
        self.assertEqual(t.get_before_execute('description'), '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  Executing: description',
            '--------------------------------------------------------------------------------',
            ''
        ]))

    def test_get_before_execute_ja(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'ホスト', 'ユーザ', self.get_exec(), handler=self.handler, encoding='utf-8', lang='ja_JP',
                     width=80)
        self.assertEqual(t.get_before_execute('メニュー 1'), '\n'.join([
            'ホスト名: ホスト                                              実行ユーザ: ユーザ',
            '================================================================================',
            '  実行: メニュー 1',
            '--------------------------------------------------------------------------------',
            ''
        ]))

    def test_get_after_execute(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler, encoding='utf-8', lang='C',
                     width=80)
        self.assertEqual(t.get_after_execute(
            'description', 123, datetime(2015, 12, 3, 4, 56, 7, 890000), datetime(2015, 12, 4, 5, 6, 7, 890000)
        ), '\n'.join([
            '--------------------------------------------------------------------------------',
            'Finished    : description',
            'Running time: 1d 0h 10m 0s  (2015-12-03 04:56:07 -> 2015-12-04 05:06:07)',
            'Return code : 123',
            '================================================================================',
            'Press any key to continue...'
        ]))

    def test_get_after_execute_ja(self):
        self.maxDiff = None

        t = Terminal({'': []}, 'host', 'user', self.get_exec(), handler=self.handler, encoding='utf-8', lang='ja_JP',
                     width=80)
        self.assertEqual(t.get_after_execute(
            'メニュー 1', 123, datetime(2015, 12, 3, 4, 56, 7, 890000), datetime(2015, 12, 4, 5, 6, 7, 890000)
        ), '\n'.join([
            '--------------------------------------------------------------------------------',
            '実行完了    : メニュー 1',
            'Running time: 1d 0h 10m 0s  (2015-12-03 04:56:07 -> 2015-12-04 05:06:07)',
            'Return code : 123',
            '================================================================================',
            '何かキーを押すとメニューに戻ります...'
        ]))

    def test_format_timedelta(self):
        self.assertEqual(Terminal._format_timedelta(timedelta(-1, 1)), '')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 0)), '0ms')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 0, 1)), '0ms')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 0, 999)), '0ms')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 0, 1000)), '1ms')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 0, 999999)), '999ms')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 1, 999)), '1s')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 60, 999)), '1m 0s')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 3600, 999)), '1h 0m 0s')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 3601, 999)), '1h 0m 1s')
        self.assertEqual(Terminal._format_timedelta(timedelta(0, 86399, 999)), '23h 59m 59s')
        self.assertEqual(Terminal._format_timedelta(timedelta(1, 0, 0)), '1d 0h 0m 0s')
        self.assertEqual(Terminal._format_timedelta(timedelta(50, 50000, 0)), '50d 13h 53m 20s')

    def test_format_datetime(self):
        self.assertEqual(Terminal._format_datetime(datetime(2015, 12, 3, 4, 56, 7, 890000)), '2015-12-03 04:56:07')

    @base_unittest.skipUnless(os.name != 'nt', 'requires POSIX compatible')
    def test_wait_input_char(self):
        _in = FakeInput('xyz\x03\n\x04')
        t = Terminal({'': []}, 'host', 'user', self.get_exec(),
                     handler=TerminalHandler(stdin=_in, keep_input_clean=False), _input=_in)
        self.assertEqual(t.wait_input_char(), 'x')
        self.assertEqual(t.wait_input_char(), 'y')
        self.assertEqual(t.wait_input_char(), 'z')
        self.assertRaises(KeyboardInterrupt, t.wait_input_char)
        self.assertEqual(t.wait_input_char(), '\n')
        self.assertRaises(KeyboardInterrupt, t.wait_input_char)

    def test_wait_input_menu(self):
        self.maxDiff = None

        _in = FakeInput('a\n9\n0\n')

        expected = '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  ',
            '--------------------------------------------------------------------------------',
            '------+-------------------------------------------------------------------------',
            '  [0] | Quit',
            '================================================================================',
            'Press menu number (0-0): ',
        ]) * 3
        with self.withAssertOutput(expected, '') as (out, err):
            t = Terminal(
                Menu('', [], Meta()), 'host', 'user', self.get_exec(encoding='utf-8', stdout=out, stderr=err),
                handler=TerminalHandler(stdin=_in, stdout=out, stderr=err, keep_input_clean=False, getch_enabled=False),
                _input=_in, _output=out, encoding='utf-8', lang='en_US', width=80, timing=False)
            t.loop()

    def test_print_source(self):
        self.maxDiff = None

        root_meta = Meta('/path/to/work', {'ENV1': 'VAL1', 'ENV2': 'VAL2'})
        sub_meta = Meta('/tmp2', {'ENV1': 'VAL1', 'ENV2': 'VAL2'})
        special_meta = Meta('/path/to/work2', {'ENV1': 'VAL9', 'ENV2': 'VAL2', 'ENV3': 'VAL3'})

        root_menu = Menu('Main menu', [
            Command('label 1', [CommandLine('command 1', root_meta)]),
            Command('label 2', [CommandLine('command 2', root_meta)]),
            Command('label 3', [CommandLine('command 3', special_meta), CommandLine('command 4', root_meta)]),
            Menu('sub menu', [
                Command('label s1', [CommandLine('command 5', sub_meta)])
            ], sub_meta),
            Command('label 9', [CommandLine('command 9', root_meta)]),
        ], root_meta)

        _in = FakeInput('s\nx\n0\n')
        path = os.path.join('tests', 'resources', 'expect', 'terminal_test_print_source.txt')
        with self.withAssertOutputFile(path, {'': ''}) as out:
            t = Terminal(
                root_menu, 'host', 'user', self.get_exec(encoding='utf-8', stdout=out, stderr=out),
                handler=TerminalHandler(stdin=_in, stdout=out, stderr=out, keep_input_clean=False, getch_enabled=False),
                _input=_in, _output=out, encoding='utf-8', lang='en_US', width=80, timing=False)
            t.loop()

    def test_print_source_ja(self):
        self.maxDiff = None

        root_meta = Meta('/path/to/work', {'ENV1': '値1', 'ENV2': '値2'})
        sub_meta = Meta('/tmp2', {'ENV1': '値1', 'ENV2': '値2'})
        special_meta = Meta('/path/to/work2', {'ENV1': '値9', 'ENV2': '値2', 'ENV3': '値3'})

        root_menu = Menu('メイン メニュー', [
            Command('メニュー 1', [CommandLine('コマンド 1', root_meta)]),
            Command('メニュー 2', [CommandLine('コマンド 2', root_meta)]),
            Command('メニュー 3', [CommandLine('コマンド 3', special_meta), CommandLine('command 4', root_meta)]),
            Menu('サブ メニュー', [
                Command('メニュー s1', [CommandLine('コマンド 5', sub_meta)])
            ], sub_meta),
            Command('メニュー 9', [CommandLine('コマンド 9', root_meta)]),
        ], root_meta)

        _in = FakeInput('s\nx\n0\n')
        path = os.path.join('tests', 'resources', 'expect', 'terminal_test_print_source_ja.txt')
        with self.withAssertOutputFile(path, {'': ''}) as out:
            t = Terminal(
                root_menu, 'host', 'user', self.get_exec(encoding='utf-8', stdout=out, stderr=out),
                handler=TerminalHandler(stdin=_in, stdout=out, stderr=out, keep_input_clean=False, getch_enabled=False),
                _input=_in, _output=out, encoding='utf-8', lang='ja_JP', width=80, timing=False)
            t.loop()

    @base_unittest.skipUnless(os.name != 'nt', 'requires POSIX compatible')
    def test_loop(self):
        self.maxDiff = None

        root_menu = Menu('Main menu', [
            Command('Menu a', [CommandLine('echo executing a', Meta())]),
            Command('Menu b', [CommandLine('echo executing b && exit 130', Meta())]),
            Menu('Sub Menu 1', [
                Command('Menu 1', [CommandLine('echo executing 1', Meta())]),
                Command('Menu 2', [CommandLine('echo executing 2', Meta())]),
                Command('Menu 3', [CommandLine('echo executing 3', Meta())]),
                Command('Menu 4', [CommandLine('echo executing 4', Meta())]),
                Command('Menu 5', [CommandLine('echo executing 5', Meta())]),
                Command('Menu 6', [CommandLine('echo executing 6', Meta())]),
                Command('Menu 7', [CommandLine('echo executing 7', Meta())]),
                Command('Menu 8', [CommandLine('echo executing 8', Meta())]),
                Command('Menu 9', [CommandLine('echo executing 9', Meta())]),
                Command('Menu 10', [CommandLine('echo executing 10', Meta())]),
            ], Meta())
        ], Meta())

        _in = FakeInput(''.join(['1n', '1N', '1\n', '1yx', '2Yx', '3n', '1yx', 'p', '9yx', '0', '-0']))

        # We use a temporary file due to capture the output of subprocess#call.
        path = os.path.join('tests', 'resources', 'expect', 'terminal_test_loop.txt')
        with self.withAssertOutputFile(path) as out:
            t = Terminal(
                root_menu, 'host', 'user', self.get_exec(encoding='utf-8', stdout=out, stderr=out),
                handler=TerminalHandler(stdin=_in, stdout=out, stderr=out, keep_input_clean=False),
                _input=_in, _output=out, encoding='utf-8', lang='en_US', width=80, timing=False)
            t.loop()

        self.assertEqual(t.executor.logger.buffer, [
            (6, '[INFO] Command started: echo executing a'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: echo executing b && exit 130'),
            (6, '[INFO] Command ended with return code: 130'),
            (6, '[INFO] Command started: echo executing 10'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: echo executing 9'),
            (6, '[INFO] Command ended with return code: 0'),
        ])

    @base_unittest.skipUnless(os.name != 'nt', 'requires POSIX compatible')
    def test_loop_sjis(self):
        self.maxDiff = None

        root_menu = Menu('メインメニュー', [Command('メニュー 1', [CommandLine("echo 'あいうえお'", Meta())])], Meta())

        _in = FakeInput(''.join(['1yx', '0']))

        # We use a temporary file due to capture the output of subprocess#call.
        path = os.path.join('tests', 'resources', 'expect', 'terminal_test_loop_sjis.txt')
        with self.withAssertOutputFile(path, expect_file_encoding='sjis', output_encoding='sjis') as out:
            t = Terminal(
                root_menu, 'ホスト', 'ユーザ', self.get_exec(encoding='sjis', stdout=out, stderr=out),
                handler=TerminalHandler(stdin=_in, stdout=out, stderr=out, keep_input_clean=False),
                _input=_in, _output=out, encoding='sjis', lang='ja_JP', width=80, timing=False)
            t.loop()
            # out.seek(0)
            # print(out.read())

        self.assertEqual(t.executor.logger.buffer, [
            (6, "[INFO] Command started: echo 'あいうえお'"),
            (6, "[INFO] Command ended with return code: 0"),
        ])

    @base_unittest.skipUnless(os.name != 'nt', 'requires POSIX compatible')
    def test_loop_multiple_commands(self):
        self.maxDiff = None

        root_menu = Menu('Main Menu', [
            Menu('Sub Menu 1', [
                Command('Menu 1', [
                    CommandLine('echo 1', Meta()),
                    CommandLine('echo 2', Meta()),
                ])
            ], Meta()),
            Menu('Sub Menu 2', [
                Menu('Sub Menu 3', [
                    Command('Menu 3', [CommandLine('echo 3', Meta())]),
                    Command('Menu 4', [CommandLine('echo 4', Meta())]),
                ], Meta()),
                Command('Menu 5', [CommandLine('echo 5', Meta())])
            ], Meta()),
            Command('Menu 6', [
                CommandLine('echo 6', Meta()),
                CommandLine('echo 7', Meta()),
                CommandLine('false', Meta()),
                CommandLine('echo 8', Meta()),
            ])
        ], Meta())

        _in = FakeInput(''.join(['1', '.1yx', '0', '21.1yx', '0.0', '3yx', '0']))

        # We use a temporary file due to capture the output of subprocess#call.
        with self.withAssertOutputFile('tests/resources/expect/terminal_test_loop_multiple_commands.txt') as out:
            t = Terminal(
                root_menu,
                'host', 'user', self.get_exec(encoding='utf-8', stdout=out, stderr=out),
                handler=TerminalHandler(stdin=_in, stdout=out, stderr=out, keep_input_clean=False),
                _input=_in, _output=out, encoding='utf-8', lang='en_US', width=80, timing=False)
            t.loop()

        self.assertEqual(t.executor.logger.buffer, [
            (6, '[INFO] Command started: echo 1'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: echo 2'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: echo 3'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: echo 6'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: echo 7'),
            (6, '[INFO] Command ended with return code: 0'),
            (6, '[INFO] Command started: false'),
            (6, '[INFO] Command ended with return code: 1'),
        ])

    def test_execute_command_duplicate(self):
        self.maxDiff = None
        sleep_cmd = 'python -c "import time;time.sleep(1)"' if os.name == 'nt' else 'sleep 1'
        _in1 = FakeInput('\n'.join(['y', '\r']))
        _in2 = FakeInput('\n'.join(['y', '\r']))

        root_menu = Menu('Main Menu', [Command('Menu 1', [CommandLine(sleep_cmd, Meta(lock=True))])])
        expected_en = '\n'.join([
            'Host: host                                                            User: user',
            '================================================================================',
            '  Confirmation',
            '--------------------------------------------------------------------------------',
            '  Would execute: Menu 1',
            '================================================================================',
            'Do you really want to execute? (y/n) [n]: '
            'Host: host                                                            User: user',
            '================================================================================',
            '  Duplicate check',
            '--------------------------------------------------------------------------------',
            '  Already running: Menu 1',
            '================================================================================',
            'Do you really want to continue? (y/n) [n]: ',
        ])

        with self.withAssertOutput(expected_en, '') as (out, err):
            t = Terminal(
                root_menu, 'host', 'user', MockExecutor(0, True),
                TerminalHandler(stdin=_in1, stdout=out, stderr=err, keep_input_clean=False, getch_enabled=False),
                _input=_in1, _output=out, encoding='utf-8', lang='en_US', width=80, timing=False)
            t.execute_command(Command('Menu 1', [CommandLine(sleep_cmd, Meta(lock=True))]))

        expected_ja = '\n'.join([
            'ホスト名: host                                                  実行ユーザ: user',
            '================================================================================',
            '  実行確認',
            '--------------------------------------------------------------------------------',
            '  Menu 1 を行います。',
            '================================================================================',
            'よろしいですか? (y/n) [n]: '
            'ホスト名: host                                                  実行ユーザ: user',
            '================================================================================',
            '  多重実行チェック',
            '--------------------------------------------------------------------------------',
            '  Menu 1 は既に実行中です。',
            '================================================================================',
            '本当によろしいですか? (y/n) [n]: ',
        ])

        with self.withAssertOutput(expected_ja, '') as (out, err):
            t = Terminal(
                root_menu, 'host', 'user', MockExecutor(0, True),
                TerminalHandler(stdin=_in2, stdout=out, stderr=err, keep_input_clean=False, getch_enabled=False),
                _input=_in2, _output=out, encoding='utf-8', lang='ja_JP', width=80, timing=False)
            t.execute_command(Command('Menu 1', [CommandLine(sleep_cmd, Meta(lock=True))]))
