export default function MetricsCard({ title, value, unit = '', trend = null, delay = 0 }) {
  return (
    <div
      className="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-800 p-4 animate-fadeInUp transition-theme hover:shadow-lg dark:hover:shadow-lg dark:hover:shadow-gray-900"
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-bold dark:text-white">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </p>
        {unit && <p className="text-sm text-gray-500 dark:text-gray-400">{unit}</p>}
      </div>
      {trend && (
        <p className={`text-xs mt-2 transition-colors ${trend > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
        </p>
      )}
    </div>
  );
}
