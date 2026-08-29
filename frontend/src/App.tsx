import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/layout/AppShell';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { MapPage } from './pages/MapPage';
import { VillageExplorerPage } from './pages/VillageExplorerPage';
import { VillageDetailPage } from './pages/VillageDetailPage';
import { CandidateAreasPage } from './pages/CandidateAreasPage';
import { MethodologyPage } from './pages/MethodologyPage';
import { SystemStatusPage } from './pages/SystemStatusPage';

// Configure TanStack Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,   // 5 minutes static data cache
      gcTime: 30 * 60 * 1000,     // 30 minutes garbage collection
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="map" element={<MapPage />} />
            <Route path="villages" element={<VillageExplorerPage />} />
            <Route path="villages/:id" element={<VillageDetailPage />} />
            <Route path="candidate-areas" element={<CandidateAreasPage />} />
            <Route path="methodology" element={<MethodologyPage />} />
            <Route path="status" element={<SystemStatusPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
