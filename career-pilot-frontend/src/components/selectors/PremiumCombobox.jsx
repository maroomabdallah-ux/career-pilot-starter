import { Check, ChevronDown, LoaderCircle, Search, X } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";

export default function PremiumCombobox({
  label,
  value,
  onChange,
  onSearchChange,
  options = [],
  placeholder = "Search…",
  loading = false,
  error,
  disabled = false,
  allowCustom = false,
  getLabel = (x) => (typeof x === "string" ? x : x.label),
  getKey = (x) => (typeof x === "string" ? x : x.value || x.id || x.label),
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const root = useRef();
  const input = useRef();
  const id = useId();
  const menuId = `combo-${id.replaceAll(":", "")}`;
  const safeLabel = (x) => {
    if (x == null) return "";
    try {
      return String(getLabel(x) ?? "");
    } catch {
      return "";
    }
  };
  const safeKey = (x) => {
    if (x == null) return "";
    try {
      return String(getKey(x) ?? safeLabel(x));
    } catch {
      return safeLabel(x);
    }
  };
  const shown = useMemo(
    () =>
      Array.isArray(options)
        ? options
            .filter((x) =>
              safeLabel(x)
                .toLocaleLowerCase()
                .includes(query.toLocaleLowerCase()),
            )
            .slice(0, 30)
        : [],
    [options, query, getLabel],
  );
  useEffect(() => {
    const close = (e) => {
      if (!root.current?.contains(e.target)) {
        setOpen(false);
        setQuery("");
        onSearchChange?.("");
      }
    };
    document.addEventListener("pointerdown", close);
    return () => document.removeEventListener("pointerdown", close);
  }, [onSearchChange]);
  useEffect(() => setActive(0), [query, options]);
  const choose = (item) => {
    onChange(item);
    setQuery("");
    onSearchChange?.("");
    setOpen(false);
    input.current?.focus();
  };
  const onKey = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((x) => Math.min(x + 1, shown.length - 1));
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((x) => Math.max(0, x - 1));
    }
    if (e.key === "Enter" && open) {
      e.preventDefault();
      if (shown[active]) choose(shown[active]);
      else if (allowCustom && query.trim()) choose(query.trim());
    }
    if (e.key === "Escape") setOpen(false);
  };
  return (
    <label className="combo-field">
      <span>{label}</span>
      <div
        ref={root}
        className={`premium-combo ${open ? "open" : ""} ${disabled ? "disabled" : ""}`}
      >
        <Search size={17} />
        <input
          ref={input}
          disabled={disabled}
          value={open ? query : value ? safeLabel(value) : ""}
          placeholder={placeholder}
          onFocus={() => {
            setOpen(true);
            setQuery("");
            onSearchChange?.("");
          }}
          onChange={(e) => {
            setQuery(e.target.value);
            onSearchChange?.(e.target.value);
            setOpen(true);
          }}
          onKeyDown={onKey}
          role="combobox"
          aria-expanded={open}
          aria-controls={menuId}
          aria-autocomplete="list"
          aria-activedescendant={
            open && shown[active] ? `${menuId}-${active}` : undefined
          }
        />
        {value ? (
          <button
            type="button"
            aria-label={`Clear ${label}`}
            onClick={() => {
              onChange(null);
              onSearchChange?.("");
            }}
          >
            <X size={15} />
          </button>
        ) : loading ? (
          <LoaderCircle className="spin" size={16} />
        ) : (
          <ChevronDown size={16} />
        )}{" "}
        {open && (
          <div className="combo-menu" id={menuId} role="listbox">
            {shown.map((item, index) => (
              <button
                id={`${menuId}-${index}`}
                type="button"
                role="option"
                aria-selected={safeKey(item) === safeKey(value)}
                className={index === active ? "active" : ""}
                key={safeKey(item)}
                onMouseDown={(e) => e.preventDefault()}
                onMouseEnter={() => setActive(index)}
                onClick={() => choose(item)}
              >
                <span>{safeLabel(item)}</span>
                {safeKey(item) === safeKey(value) && <Check size={15} />}
              </button>
            ))}
            {allowCustom &&
              query.trim() &&
              !shown.some(
                (x) =>
                  safeLabel(x).toLocaleLowerCase() ===
                  query.toLocaleLowerCase(),
              ) && (
                <button
                  type="button"
                  onMouseDown={(e) => e.preventDefault()}
                  onClick={() => choose(query.trim())}
                >
                  <span>Use “{query.trim()}”</span>
                  <small>Custom entry</small>
                </button>
              )}
            {!loading && !shown.length && !query.trim() && (
              <p>Start typing to search</p>
            )}
            {!loading && !shown.length && query.trim() && !allowCustom && (
              <p>No matching options</p>
            )}
            {error && <p>{error}</p>}
          </div>
        )}
      </div>
      {error && !open && (
        <small className="selector-error" role="status">
          {error}
        </small>
      )}
    </label>
  );
}
