export default function ConfidenceBadge({ value }) {
  const getStyles = (val) => {
    if (val > 80) return { bg: "rgba(16, 185, 129, 0.15)", text: "#10b981" };
    if (val >= 50) return { bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b" };
    return { bg: "rgba(239, 68, 68, 0.15)", text: "#ef4444" };
  };

  const style = getStyles(value);

  return (
    <span style={{
      background: style.bg,
      color: style.text,
      padding: "6px 12px",
      borderRadius: "20px",
      fontSize: "11px",
      fontWeight: "800",
      border: `1px solid ${style.text}`,
      textTransform: "uppercase",
      letterSpacing: "0.5px"
    }}>
      {value}% Confidence
    </span>
  );
}