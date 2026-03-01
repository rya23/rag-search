import { ChatInterface } from "@/components/chat/ChatInterface";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";

export default function Home() {
  return (
    <SidebarProvider defaultOpen>
      <AppSidebar />
      <SidebarInset>
        <ChatInterface />
      </SidebarInset>
    </SidebarProvider>
  );
}
