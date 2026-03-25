export function Skeleton({ className = '' }) {
  return (
    <div
      className={`animate-pulse bg-surface-variant rounded ${className}`}
    />
  );
}

export function SkeletonChart() {
  return (
    <div className="space-y-4 p-6 bg-surface-container rounded-lg border border-outline-variant animate-fadeInUp">
      <Skeleton className="h-6 w-1/3" />
      <div className="space-y-2">
        {Array(3).fill(0).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  );
}

export function SkeletonMetrics() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array(4).fill(0).map((_, i) => (
        <div
          key={i}
          className="bg-surface-container rounded-lg border border-outline-variant p-4 animate-fadeInUp"
          style={{ animationDelay: `${i * 50}ms` }}
        >
          <Skeleton className="h-4 w-1/2 mb-3" />
          <Skeleton className="h-8 w-1/3 mb-2" />
          <Skeleton className="h-3 w-2/3" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonTable() {
  return (
    <div className="space-y-3 bg-surface-container rounded-lg border border-outline-variant p-4">
      <div className="space-y-2">
        {Array(5).fill(0).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    </div>
  );
}
