# Shim module to forward resource registration to the main icons resource
# This keeps generated UI files that `import mail_icon_rc` working after the
# mail icon was moved into `Icons/Main_Icons.qrc` which compiles to `Main_Icons_rc`.
try:
    import Main_Icons_rc  # registers :/Main_Window/Icons/... resources
except Exception:
    # As a fallback, try local Icons package
    try:
        from Icons import Main_Icons_rc as Main_Icons_rc  # type: ignore
    except Exception:
        # If resources are not available, ignore — UI will handle missing pixmap
        pass
