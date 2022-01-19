#!/usr/bin/env python3

import os
import shutil
import tempfile

import unittest
from unittest import mock

import cantools


class CanToolsConvertFullTest(unittest.TestCase):

    SYM_FILE_COMMENTS_HEX_AND_MOTOROLA = os.path.join(os.path.split(__file__)[0], 'files', 'sym', 'comments_hex_and_motorola.sym')
    DBC_FILE_COMMENTS_HEX_AND_MOTOROLA = os.path.join(os.path.split(__file__)[0], 'files', 'dbc', 'comments_hex_and_motorola_converted_from_sym.dbc')

    maxDiff = None

    # ------- aux functions -------

    def get_out_file_name(self, fn_in, ext):
        fn = fn_in
        fn = os.path.splitext(fn)[0] + ext
        fn = os.path.split(fn)[1]
        fn = os.path.join(tempfile.mkdtemp(), fn)
        return fn

    def assertFileEqual(self, fn1, fn2, encoding=None):
        with open(fn1, 'rt', encoding=encoding) as f:
            content1 = list(f)
        with open(fn2, 'rt', encoding=encoding) as f:
            content2 = list(f)
        self.assertListEqual(content1, content2)

    def assertDatabaseEqual(self, db1, db2, *, ignore_message_attributes=[], ignore_signal_attributes=[]):
        message_attributes = ("name", "frame_id", "is_extended_frame", "length", "comment")
        signal_attributes = ("name", "start", "length", "byte_order", "is_signed", "is_float",
                             "initial", "scale", "offset", "minimum", "maximum", "unit", "comment",
                             "choices", "is_multiplexer", "multiplexer_ids", "multiplexer_signal")
        self.assertEqual(len(db1.messages), len(db2.messages))
        for i in range(len(db1.messages)):
            msg1 = db1.messages[i]
            msg2 = db2.messages[i]
            for a in message_attributes:
                if a in ignore_message_attributes:
                    continue
                print(f"msg.{a}".ljust(30) + str(getattr(msg1, a)).ljust(10) + " == %s" % getattr(msg2, a))
                self.assertEqual(getattr(msg1, a), getattr(msg2, a), "%s does not match for message %s" % (a, i))

            self.assertEqual(len(msg1.signals), len(msg2.signals))
            sort = lambda s: (s.start, s.multiplexer_ids)
            for sig1, sig2 in zip(sorted(msg1.signals, key=sort), sorted(msg2.signals, key=sort)):
                for a in signal_attributes:
                    if a in ignore_signal_attributes:
                        continue
                    print("    "+f"sig.{a}".ljust(30) + str(getattr(sig1, a)).ljust(10) + " == %s" % getattr(sig2, a))
                    self.assertEqual(getattr(sig1, a), getattr(sig2, a), "%s does not match for signal %s in message %s" % (a, sig1.name, msg1.name))

                print()

    def remove_out_file(self, fn_out):
        path = os.path.split(fn_out)[0]
        shutil.rmtree(path)

    # ------- dump, load, dump produces same output -------

    def test_dbc_load_and_dump(self):
        filename = 'tests/files/dbc/socialledge-written-by-cantools.dbc'
        fn_out = self.get_out_file_name(filename, ext='.dbc')
        fn_expected_output = filename

        db = cantools.database.load_file(filename, prune_choices=False, sort_signals=None)
        cantools.database.dump_file(db, fn_out)

        self.assertFileEqual(fn_expected_output, fn_out)
        self.remove_out_file(fn_out)

    # ------- sort_signals when dumping to dbc files -------

    def test_dbc_dump_sort_signals_by_name(self):
        fn_in = 'tests/files/dbc/socialledge-written-by-cantools.dbc'
        fn_expected_output = 'tests/files/dbc/socialledge-written-by-cantools-with-sort-signals-by-name.dbc'
        sort_signals = lambda signals: list(sorted(signals, key=lambda sig: sig.name))
        fn_out = self.get_out_file_name(fn_expected_output, ext='.dbc')

        db = cantools.database.load_file(fn_in, prune_choices=False)
        cantools.database.dump_file(db, fn_out, sort_signals=sort_signals)

        self.assertFileEqual(fn_expected_output, fn_out)
        self.remove_out_file(fn_out)

    def test_dbc_dump_default_sort_signals(self):
        fn_in = 'tests/files/dbc/socialledge-written-by-cantools.dbc'
        fn_expected_output = 'tests/files/dbc/socialledge-written-by-cantools-with-default-sort-signals.dbc'
        fn_out = self.get_out_file_name(fn_expected_output, ext='.dbc')

        db = cantools.database.load_file(fn_in, prune_choices=False)
        cantools.database.dump_file(db, fn_out)

        self.assertFileEqual(fn_expected_output, fn_out)
        self.remove_out_file(fn_out)

    def test_dbc_dump_default_sort_signals2(self):
        fn_in = 'tests/files/dbc/vehicle.dbc'
        fn_out1 = self.get_out_file_name("loaded-with-default-sort-signals", ext='.dbc')
        fn_out2 = self.get_out_file_name("loaded-with-sort-signals-by-name", ext='.dbc')

        db1 = cantools.database.load_file(fn_in)
        db2 = cantools.database.load_file(fn_in, sort_signals = lambda signals: list(sorted(signals, key=lambda sig: sig.name)))

        msg1 = db1.get_message_by_name('RT_DL1MK3_GPS_Speed')
        msg2 = db2.get_message_by_name('RT_DL1MK3_GPS_Speed')

        self.assertEqual({repr(s) for s in msg1.signals}, {repr(s) for s in msg2.signals})
        self.assertNotEqual([repr(s) for s in msg1.signals], [repr(s) for s in msg2.signals])

        cantools.database.dump_file(db1, fn_out1)
        cantools.database.dump_file(db2, fn_out2)

        self.assertFileEqual(fn_out1, fn_out2, encoding='cp1252')
        self.remove_out_file(fn_out1)
        self.remove_out_file(fn_out2)

    # ------- sort_signals when dumping to kcd files -------

    def test_kcd_dump_default_sort_signals(self):
        fn_in = 'tests/files/kcd/vehicle.kcd'
        fn_expected_output = fn_in
        fn_out = self.get_out_file_name(fn_expected_output, ext='.kcd')

        db = cantools.database.load_file(fn_in, prune_choices=False)
        cantools.database.dump_file(db, fn_out)

        self.assertFileEqual(fn_expected_output, fn_out)
        self.remove_out_file(fn_out)

        for msg in db.messages:
            msg.signals.sort(key=lambda sig: sig.name)

        fn_expected_output = 'tests/files/kcd/vehicle-sort-signals-by-name.kcd'
        fn_out = self.get_out_file_name(fn_expected_output, ext='.kcd')
        cantools.database.dump_file(db, fn_out)

        self.assertFileEqual(fn_expected_output, fn_out)
        self.remove_out_file(fn_out)

    def test_kcd_dump_sort_signals_by_name(self):
        fn_in = 'tests/files/kcd/vehicle.kcd'
        fn_expected_output = 'tests/files/kcd/vehicle-sort-signals-by-name.kcd'
        fn_out = self.get_out_file_name(fn_expected_output, ext='.kcd')
        sort_signals = lambda signals: list(sorted(signals, key=lambda sig: sig.name))

        db = cantools.database.load_file(fn_in, prune_choices=False)
        cantools.database.dump_file(db, fn_out, sort_signals=sort_signals)

        self.assertFileEqual(fn_expected_output, fn_out)
        self.remove_out_file(fn_out)

    # ------- test sym -> dbc -------

    def test_sym_to_dbc__compare_files(self):
        sym = self.SYM_FILE_COMMENTS_HEX_AND_MOTOROLA
        dbc = self.DBC_FILE_COMMENTS_HEX_AND_MOTOROLA
        fn_out = self.get_out_file_name(sym, ext='.dbc')
        argv = ['cantools', 'convert', sym, fn_out]

        with mock.patch('sys.argv', argv):
            cantools._main()

        fn_expected_output = dbc
        self.assertFileEqual(fn_expected_output, fn_out)

        self.remove_out_file(fn_out)

    def test_sym_to_dbc__compare_databases(self):
        sym = self.SYM_FILE_COMMENTS_HEX_AND_MOTOROLA
        dbc = self.DBC_FILE_COMMENTS_HEX_AND_MOTOROLA
        sym = cantools.database.load_file(sym)
        dbc = cantools.database.load_file(dbc)
        # In the sym file some maximum values are given but no minimum values.
        # In dbc files it does not seem to be possible to specify only one of both.
        # Therefore sig12 and sig22 have minimum = None in the sym file but minimum = 0 in the dbc file.
        # Therefore I am ignoring minimum values in this test.
        self.assertDatabaseEqual(sym, dbc, ignore_signal_attributes=['minimum'])


if __name__ == '__main__':
    unittest.main()
