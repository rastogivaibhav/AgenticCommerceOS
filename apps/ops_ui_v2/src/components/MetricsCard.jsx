const CARD_TOKENS = [
  { bg: 'bg-primary-container', text: 'text-on-primary-container' },
  { bg: 'bg-secondary-container', text: 'text-on-secondary-container' },
  { bg: 'bg-tertiary-container', text: 'text-on-tertiary-container' },
  { bg: 'bg-surface-container-high', text: 'text-on-surface' },
];

export default function MetricsCard({ title, value, unit = '', trend = null, delay = 0, index = 0 }) {
  const { bg, text } = CARD_TOKENS[index % 4];
  return (
    <div
      className={`${bg} ${text} rounded-[24px] border border-outline-variant p-5 shadow-sm animate-fadeInUp`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-xs font-extrabold uppercase tracking-[0.14em] opacity-75">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-extrabold tracking-tight">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </p>
        {unit && <p className="text-sm opacity-70">{unit}</p>}
      </div>
      {trend != null && (
        <p className={`mt-3 text-xs font-semibold ${trend > 0 ? 'text-on-success-container' : 'text-on-error-container'}`}>
          {trend > 0 ? 'Up' : 'Down'} {Math.abs(trend)}% from last period
        </p>
      )}
    </div>
  );
}
