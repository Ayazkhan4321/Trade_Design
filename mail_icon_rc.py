# Top-level shim so generated UI files that do `import mail_icon_rc` can
# work regardless of where the resources live. Forward to `Forgot_password.mail_icon_rc`.
try:
    from Forgot_password import mail_icon_rc as _shim  # noqa: F401
except Exception:
    # If that fails, try to forward to Icons.Main_Icons_rc directly
    try:
        import Main_Icons_rc as _shim  # noqa: F401
    except Exception:
        try:
            from Icons import Main_Icons_rc as _shim  # noqa: F401
        except Exception:
            pass
