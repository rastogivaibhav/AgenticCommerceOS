const CARD_TOKENS = [
  { bg: 'bg-primary-container',      text: 'text-on-primary-container' },
  { bg: 'bg-secondary-container',    text: 'text-on-secondary-container' },
  { bg: 'bg-warning-container',      text: 'text-on-warning-container' },
  { bg: 'bg-surface-container-high', text: 'text-on-surface' },
];

export default function MetricsCard({ title, value, unit = '', trend = null, delay = 0, index = 0 }) {
  const { bg, text } = CARD_TOKENS[index % 4];
  return (
    <div
      className={`${bg} ${text} rounded-2xl p-5 animate-fadeInUp`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-sm font-medium uppercase tracking-wide opacity-80">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-bold">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </p>
        {unit && <p className="text-sm opacity-70">{unit}</p>}
      </div>
      {trend != null && (
        <p className={`text-xs mt-2 font-medium ${trend > 0 ? 'text-on-success-container' : 'text-on-error-container'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
        </p>
      )}
    </div>
  );
}
