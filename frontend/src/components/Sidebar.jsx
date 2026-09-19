import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Library, Settings } from 'lucide-react';

export default function Sidebar() {
  const location = useLocation();

  const links = [
    { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
    { name: 'Content Library', path: '/library', icon: <Library size={20} /> },
    { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
  ];

  return (
    <div className="w-64 h-screen bg-foreground text-background flex flex-col">
      <div className="p-6">
        <h1 className="text-xl font-bold tracking-tight text-accent">iAgent Solutions</h1>
        <p className="text-sm text-gray-400 mt-1">Content OS</p>
      </div>
      <nav className="flex-1 px-4 mt-6">
        <ul className="space-y-2">
          {links.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <li key={link.name}>
                <Link
                  to={link.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                    isActive ? 'bg-accent text-white font-medium' : 'text-gray-300 hover:bg-gray-800'
                  }`}
                >
                  {link.icon}
                  {link.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="p-6 text-xs text-gray-500">
        v1.0.0 Alpha
      </div>
    </div>
  );
}
