import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: number;
  icon: LucideIcon;
  color: 'blue' | 'purple' | 'green' | 'orange';
}

const colorClasses = {
  blue: 'bg-blue-500 text-blue-600 bg-blue-50',
  purple: 'bg-purple-500 text-purple-600 bg-purple-50',
  green: 'bg-green-500 text-green-600 bg-green-50',
  orange: 'bg-orange-500 text-orange-600 bg-orange-50',
};

const StatsCard = ({ title, value, icon: Icon, color }: StatsCardProps) => {
  const [, textColor, cardBg] = colorClasses[color].split(' ');

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 rounded-lg ${cardBg}`}>
          <Icon className={`w-6 h-6 ${textColor}`} />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );
};

export default StatsCard;