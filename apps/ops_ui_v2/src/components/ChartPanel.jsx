import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const CHART_COLORS = ['#175cd3', '#0f766e', '#b54708'];

const tooltipStyle = {
  backgroundColor: 'rgba(255, 255, 255, 0.96)',
  border: '1px solid #d0d5dd',
  borderRadius: 16,
  boxShadow: '0 18px 40px rgba(16, 24, 40, 0.14)',
  color: '#101828',
};

export default function ChartPanel({ title, data, type = 'line', xKey, yKeys = [] }) {
  const chartProps = {
    data,
    margin: { top: 10, right: 12, left: -12, bottom: 2 },
  };

  return (
    <div className="bg-transparent">
      <div className="mb-4">
        <h3 className="text-lg font-extrabold tracking-tight text-on-surface">{title}</h3>
        <p className="mt-1 text-sm text-on-surface-variant">
          Operational trend view for the currently available control-plane data.
        </p>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        {type === 'line' ? (
          <LineChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e7ec" vertical={false} />
            <XAxis dataKey={xKey} stroke="#667085" tickLine={false} axisLine={false} />
            <YAxis stroke="#667085" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            {yKeys.map((key, idx) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={CHART_COLORS[idx % CHART_COLORS.length]}
                strokeWidth={3}
                dot={{ r: 0 }}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        ) : (
          <BarChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e4e7ec" vertical={false} />
            <XAxis dataKey={xKey} stroke="#667085" tickLine={false} axisLine={false} />
            <YAxis stroke="#667085" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend />
            {yKeys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                fill={CHART_COLORS[idx % CHART_COLORS.length]}
                radius={[8, 8, 0, 0]}
              />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
