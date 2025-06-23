import { Link } from 'react-router-dom';
import { LucideIcon } from 'lucide-react';

interface ActionButtonProps {
  title: string;
  description: string;
  icon: LucideIcon;
  color: 'blue' | 'green' | 'purple' | 'orange';
  href: string;
}

const colorClasses = {
  blue: 'border-blue-200 hover:border-blue-300 text-blue-600 bg-blue-50',
  green: 'border-green-200 hover:border-green-300 text-green-600 bg-green-50',
  purple: 'border-purple-200 hover:border-purple-300 text-purple-600 bg-purple-50',
  orange: 'border-orange-200 hover:border-orange-300 text-orange-600 bg-orange-50',
};

const ActionButton = ({ title, description, icon: Icon, color, href }: ActionButtonProps) => {
  const colorClass = colorClasses[color];

  return (
    <Link
      to={href}
      className={`block p-4 border-2 rounded-lg transition-colors ${colorClass}`}
    >
      <div className="flex items-center">
        <Icon className="w-8 h-8 mr-3" />
        <div>
          <h3 className="font-semibold text-gray-900">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
    </Link>
  );
};

export default ActionButton;