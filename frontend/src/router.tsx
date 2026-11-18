import React, { createContext, useContext, useState, useEffect } from 'react';

interface RouterContextType {
  path: string;
  navigate: (to: string) => void;
}

const RouterContext = createContext<RouterContextType>({
  path: window.location.pathname,
  navigate: () => { },
});

export const useRouter = () => useContext(RouterContext);

export const useNavigate = () => {
  const { navigate } = useRouter();
  return navigate;
};

export const useParams = <T extends Record<string, string>>(): T => {
  const { path } = useRouter();
  const segments = path.split('?')[0].split('/').filter(Boolean);

  // Custom route parameter matcher for vehicles, stations, chargers, reservations, sessions, invoices, payments, and maintenance
  if ((segments[0] === 'vehicles' || segments[0] === 'stations' || segments[0] === 'chargers' || segments[0] === 'reservations' || segments[0] === 'sessions' || segments[0] === 'invoices' || segments[0] === 'payments' || segments[0] === 'maintenance') && segments[1] && segments[1] !== 'add' && segments[1] !== 'new' && segments[1] !== 'start' && segments[1] !== 'active' && segments[1] !== 'history' && segments[1] !== 'reports' && segments[1] !== 'requests' && segments[1] !== 'analytics') {
    return { id: segments[1] } as unknown as T;
  }
  return {} as T;
};

export const useSearchParams = (): [URLSearchParams, (params: URLSearchParams) => void] => {
  const search = window.location.search;
  const params = new URLSearchParams(search);
  const setSearchParams = (newParams: URLSearchParams) => {
    const newUrl = `${window.location.pathname}?${newParams.toString()}`;
    window.history.pushState({}, '', newUrl);
  };
  return [params, setSearchParams];
};

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string;
  children: React.ReactNode;
}

export const Link: React.FC<LinkProps> = ({ to, children, style, className, onClick, ...rest }) => {
  const navigate = useNavigate();
  return (
    <a
      href={to}
      style={style}
      className={className}
      onClick={(e) => {
        if (onClick) onClick(e);
        if (!e.defaultPrevented && e.button === 0 && !e.metaKey && !e.ctrlKey) {
          e.preventDefault();
          navigate(to);
        }
      }}
      {...rest}
    >
      {children}
    </a>
  );
};

export const BrowserRouter: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [path, setPath] = useState<string>(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (to: string) => {
    window.history.pushState({}, '', to);
    setPath(to);
    window.scrollTo(0, 0);
  };

  return (
    <RouterContext.Provider value={{ path, navigate }}>
      {children}
    </RouterContext.Provider>
  );
};

