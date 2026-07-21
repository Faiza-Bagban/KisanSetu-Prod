import RiskBadge from '../components/RiskBadge';

export default function BadgeTest() {
  return (
    <div style={{ padding: '40px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <h2>RiskBadge Component Test</h2>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <RiskBadge level="HIGH"   percent={99.8} />
        <RiskBadge level="MEDIUM" percent={52.3} />
        <RiskBadge level="LOW"    percent={1.4}  />
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span>Small:</span>
        <RiskBadge level="HIGH"   percent={99.8} size="sm" />
        <RiskBadge level="MEDIUM" percent={52.3} size="sm" />
        <RiskBadge level="LOW"    percent={1.4}  size="sm" />
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span>Large:</span>
        <RiskBadge level="HIGH"   percent={99.8} size="lg" />
        <RiskBadge level="MEDIUM" percent={52.3} size="lg" />
        <RiskBadge level="LOW"    percent={1.4}  size="lg" />
      </div>

      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <span>No percent:</span>
        <RiskBadge level="HIGH"   showPercent={false} />
        <RiskBadge level="MEDIUM" showPercent={false} />
        <RiskBadge level="LOW"    showPercent={false} />
      </div>
    </div>
  );
}