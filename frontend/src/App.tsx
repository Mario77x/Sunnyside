import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import Index from "./pages/Index";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import CreateActivity from "./pages/CreateActivity";
import WeatherPlanning from "./pages/WeatherPlanning";
import InviteGuests from "./pages/InviteGuests";
import GuestResponse from "./pages/GuestResponse";
import GuestPreview from "./pages/GuestPreview";
import InviteeResponse from "./pages/InviteeResponse";
import ResponseReview from "./pages/ResponseReview";
import VenuePoll from "./pages/VenuePoll";
import PostActivityFeedback from "./pages/PostActivityFeedback";
import Account from "./pages/Account";
import ActivitySummary from "./pages/ActivitySummary";
import InviteeActivitySummary from "./pages/InviteeActivitySummary";
import ActivityRecommendations from "./pages/ActivityRecommendations";
import ActivitySuggestions from "./pages/ActivitySuggestions";
import FinalizationPage from "./pages/FinalizationPage";
import FinalizationSummary from "./pages/FinalizationSummary";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/login" element={<Login />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/create-activity" element={<CreateActivity />} />
            <Route path="/weather-planning" element={<WeatherPlanning />} />
            <Route path="/activity-recommendations" element={<ActivityRecommendations />} />
            <Route path="/activity-suggestions" element={<ActivitySuggestions />} />
            <Route path="/invite-guests" element={<InviteGuests />} />
            <Route path="/guest/:activityId" element={<GuestResponse />} />
            <Route path="/guest-preview/:activityId" element={<GuestPreview />} />
            <Route path="/invitee-response" element={<InviteeResponse />} />
            <Route path="/response-review" element={<ResponseReview />} />
            <Route path="/venue-poll" element={<VenuePoll />} />
            <Route path="/post-activity-feedback" element={<PostActivityFeedback />} />
            <Route path="/account" element={<Account />} />
            <Route path="/activity-summary" element={<ActivitySummary />} />
            <Route path="/invitee-activity-summary" element={<InviteeActivitySummary />} />
            <Route path="/finalize-activity" element={<FinalizationPage />} />
            <Route path="/finalization-summary" element={<FinalizationSummary />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;