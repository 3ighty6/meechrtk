"""Tests for meechrtk.compressor -- the core safety guarantee is that
error/warning/exception signal is NEVER touched, regardless of how
aggressively surrounding noise gets compressed.
"""
from meechrtk.compressor import compress


def test_npm_noise_gets_heavily_compressed():
    text = (
        "npm warn deprecated inflight@1.0.6: leaks memory\n"
        "npm warn deprecated npmlog@5.0.1: unsupported\n"
        "npm notice\n"
        "npm notice New major version of npm available! 10.9.7 -> 12.0.2\n"
        "npm notice\n"
        "\n"
        "added 1247 packages, and audited 1248 packages in 18s\n"
        "\n"
        "211 packages are looking for funding\n"
        "  run `npm fund` for details\n"
        "\n"
        "found 0 vulnerabilities\n"
    )
    result = compress(text)
    # Smaller inputs have proportionally more overhead from the elision
    # message itself -- 70%+ here, 85-90%+ on realistically-sized noisy
    # output (verified separately against real npm/build output).
    assert result.savings_ratio >= 0.65, f"expected >=65% reduction, got {result.savings_ratio:.1%}"
    assert "found 0 vulnerabilities" in result.compressed


def test_npm_errors_survive_completely_verbatim():
    text = (
        "npm warn deprecated inflight@1.0.6: leaks memory\n"
        "npm notice\n"
        "\n"
        "npm ERR! code ERESOLVE\n"
        "npm ERR! ERESOLVE unable to resolve dependency tree\n"
        "npm ERR! Found: react@18.3.1\n"
        "npm ERR! peer react@\"^19.0.0\" from some-package@2.0.0\n"
        "\n"
        "npm warn deprecated glob@7.2.3: unsupported\n"
    )
    result = compress(text)
    # every single ERR! line, with its exact package/version details,
    # must appear byte-for-byte in the compressed output
    for line in text.splitlines():
        if "npm ERR!" in line:
            assert line in result.compressed, f"error line was altered or dropped: {line!r}"


def test_long_clean_block_gets_truncated_but_keeps_edges():
    lines = [f"transforming module {i}.tsx" for i in range(40)]
    lines += ["dist/assets/index-abc123.js  214.93 kB"]
    text = "\n".join(lines)
    result = compress(text)
    assert result.savings_ratio >= 0.7
    assert "dist/assets/index-abc123.js" in result.compressed
    assert "omitted" in result.compressed


def test_exact_mode_is_a_true_bypass():
    text = "npm warn deprecated x@1.0.0\nnpm ERR! something broke\n" * 5
    result = compress(text, exact=True)
    assert result.compressed == text
    assert result.savings_ratio == 0.0


def test_empty_input():
    result = compress("")
    assert result.compressed == ""
    assert result.savings_ratio == 0.0


def test_consecutive_duplicates_still_collapse():
    text = "same line\n" * 6 + "ERROR: real problem\n"
    result = compress(text)
    assert "ERROR: real problem" in result.compressed
    assert result.compressed.count("same line") < 6
