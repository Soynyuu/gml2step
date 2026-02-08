"""Tests for citygml/utils/logging.py — Thread-local logging utilities."""

import io
import threading

import pytest

from gml2step.citygml.utils.logging import (
    log,
    set_log_file,
    close_log_file,
    get_log_file,
    _thread_local,
)


class TestLog:
    """Tests for log() function."""

    def setup_method(self):
        """Ensure clean state before each test."""
        set_log_file(None)

    def teardown_method(self):
        """Ensure clean state after each test."""
        set_log_file(None)

    def test_log_prints_to_stdout(self, capsys):
        log("hello world")
        captured = capsys.readouterr()
        assert "hello world" in captured.out

    def test_log_writes_to_file_when_set(self):
        buf = io.StringIO()
        set_log_file(buf)
        log("file message")
        assert "file message\n" in buf.getvalue()

    def test_log_does_not_write_to_file_when_unset(self, capsys):
        log("console only")
        captured = capsys.readouterr()
        assert "console only" in captured.out

    def test_log_writes_newline_to_file(self):
        buf = io.StringIO()
        set_log_file(buf)
        log("line1")
        log("line2")
        lines = buf.getvalue().split("\n")
        assert lines[0] == "line1"
        assert lines[1] == "line2"

    def test_log_flushes_after_write(self):
        """Verify flush is called (StringIO is always flushed, but check write happened)."""
        buf = io.StringIO()
        set_log_file(buf)
        log("flushed")
        assert buf.getvalue() == "flushed\n"

    def test_log_silently_ignores_closed_file(self, capsys):
        """log() should not raise even if file is closed."""
        buf = io.StringIO()
        set_log_file(buf)
        buf.close()
        # Should not raise
        log("after close")
        captured = capsys.readouterr()
        assert "after close" in captured.out


class TestSetLogFile:
    """Tests for set_log_file()."""

    def teardown_method(self):
        set_log_file(None)

    def test_set_log_file_stores_file(self):
        buf = io.StringIO()
        set_log_file(buf)
        assert get_log_file() is buf

    def test_set_log_file_none_clears(self):
        buf = io.StringIO()
        set_log_file(buf)
        set_log_file(None)
        assert get_log_file() is None

    def test_set_log_file_replaces_previous(self):
        buf1 = io.StringIO()
        buf2 = io.StringIO()
        set_log_file(buf1)
        set_log_file(buf2)
        assert get_log_file() is buf2


class TestCloseLogFile:
    """Tests for close_log_file()."""

    def teardown_method(self):
        set_log_file(None)

    def test_close_log_file_clears_reference(self):
        buf = io.StringIO()
        set_log_file(buf)
        close_log_file()
        assert get_log_file() is None

    def test_close_log_file_closes_file(self):
        buf = io.StringIO()
        set_log_file(buf)
        close_log_file()
        assert buf.closed

    def test_close_log_file_safe_when_no_file(self):
        """Should not raise when no file is set."""
        close_log_file()

    def test_close_log_file_safe_when_already_closed(self):
        """Should not raise when file is already closed."""
        buf = io.StringIO()
        set_log_file(buf)
        buf.close()
        close_log_file()  # Should not raise

    def test_close_log_file_idempotent(self):
        """Calling close_log_file() twice should not raise."""
        buf = io.StringIO()
        set_log_file(buf)
        close_log_file()
        close_log_file()


class TestGetLogFile:
    """Tests for get_log_file()."""

    def teardown_method(self):
        set_log_file(None)

    def test_returns_none_initially(self):
        set_log_file(None)
        assert get_log_file() is None

    def test_returns_set_file(self):
        buf = io.StringIO()
        set_log_file(buf)
        assert get_log_file() is buf


class TestThreadIsolation:
    """Tests for thread-local storage isolation."""

    def teardown_method(self):
        set_log_file(None)

    def test_different_threads_have_separate_log_files(self):
        """Each thread should have its own log file."""
        main_buf = io.StringIO()
        thread_buf = io.StringIO()
        results = {}

        set_log_file(main_buf)

        def thread_fn():
            set_log_file(thread_buf)
            log("from thread")
            results["thread_file"] = get_log_file()
            results["thread_content"] = thread_buf.getvalue()
            # Don't close thread_buf here so main thread can verify
            set_log_file(None)

        t = threading.Thread(target=thread_fn)
        t.start()
        t.join()

        # Main thread log file should be unaffected
        assert get_log_file() is main_buf
        # Thread had its own file
        assert results["thread_file"] is thread_buf
        assert "from thread\n" in results["thread_content"]

    def test_thread_log_does_not_affect_main(self):
        """Writing in a thread should not affect main thread's log file."""
        main_buf = io.StringIO()
        set_log_file(main_buf)

        def thread_fn():
            log("thread message")  # No file set in this thread

        t = threading.Thread(target=thread_fn)
        t.start()
        t.join()

        # Main thread's buffer should NOT have thread message
        assert "thread message" not in main_buf.getvalue()

        set_log_file(None)
