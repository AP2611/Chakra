import { User, Key, Bell, Palette, Shield, HelpCircle, Moon, Sun, Monitor } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTheme } from "@/components/theme/ThemeProvider";

interface SettingsSectionProps {
  title: string;
  description: string;
  icon: React.ElementType;
  children: React.ReactNode;
}

function SettingsSection({ title, description, icon: Icon, children }: SettingsSectionProps) {
  return (
    <div className="card-elevated p-6">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-10 h-10 rounded-lg bg-accent flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-accent-foreground" />
        </div>
        <div>
          <h3 className="section-title">{title}</h3>
          <p className="section-subtitle mt-1">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

interface SettingRowProps {
  label: string;
  description?: string;
  children: React.ReactNode;
}

function SettingRow({ label, description, children }: SettingRowProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        {description && (
          <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}

interface ToggleSwitchProps {
  enabled: boolean;
  onChange: () => void;
}

function ToggleSwitch({ enabled, onChange }: ToggleSwitchProps) {
  return (
    <button
      onClick={onChange}
      className={cn(
        "w-11 h-6 rounded-full transition-colors relative",
        enabled ? "bg-primary" : "bg-secondary"
      )}
    >
      <span
        className={cn(
          "absolute top-1 w-4 h-4 rounded-full bg-white shadow-sm transition-transform",
          enabled ? "translate-x-6" : "translate-x-1"
        )}
      />
    </button>
  );
}

type Theme = "light" | "dark" | "system";

interface ThemeOptionProps {
  value: Theme;
  current: Theme;
  label: string;
  icon: React.ElementType;
  onClick: (theme: Theme) => void;
}

function ThemeOption({ value, current, label, icon: Icon, onClick }: ThemeOptionProps) {
  const isActive = current === value;
  return (
    <button
      onClick={() => onClick(value)}
      className={cn(
        "flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200",
        isActive 
          ? "border-primary bg-accent" 
          : "border-border hover:border-primary/50 hover:bg-accent/50"
      )}
    >
      <Icon className={cn("w-5 h-5", isActive ? "text-primary" : "text-muted-foreground")} />
      <span className={cn("text-sm font-medium", isActive ? "text-foreground" : "text-muted-foreground")}>
        {label}
      </span>
    </button>
  );
}

export function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen p-8 lg:p-12">
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold text-foreground">Settings</h1>
          <p className="text-muted-foreground">
            Manage your workspace preferences and account settings
          </p>
        </div>

        {/* Profile Section */}
        <SettingsSection
          title="Profile"
          description="Manage your account information"
          icon={User}
        >
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary to-gold flex items-center justify-center text-primary-foreground text-xl font-semibold glow-warm">
                JD
              </div>
              <div>
                <p className="font-medium text-foreground">John Doe</p>
                <p className="text-sm text-muted-foreground">john.doe@company.com</p>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Edit Profile
            </Button>
          </div>
        </SettingsSection>

        {/* Appearance Section */}
        <SettingsSection
          title="Appearance"
          description="Customize the look and feel"
          icon={Palette}
        >
          <div className="space-y-4">
            <SettingRow label="Theme" description="Choose your preferred color scheme">
              <div className="flex gap-3">
                <ThemeOption
                  value="light"
                  current={theme}
                  label="Light"
                  icon={Sun}
                  onClick={setTheme}
                />
                <ThemeOption
                  value="dark"
                  current={theme}
                  label="Dark"
                  icon={Moon}
                  onClick={setTheme}
                />
                <ThemeOption
                  value="system"
                  current={theme}
                  label="System"
                  icon={Monitor}
                  onClick={setTheme}
                />
              </div>
            </SettingRow>
            <SettingRow
              label="Compact mode"
              description="Reduce spacing for more content"
            >
              <ToggleSwitch enabled={false} onChange={() => {}} />
            </SettingRow>
          </div>
        </SettingsSection>

        {/* API Keys Section */}
        <SettingsSection
          title="API Keys"
          description="Manage your API keys and integrations"
          icon={Key}
        >
          <div className="space-y-0">
            <SettingRow
              label="Production API Key"
              description="Used for production environments"
            >
              <div className="flex items-center gap-2">
                <code className="text-xs bg-secondary px-2 py-1 rounded font-mono">
                  chk_••••••••••••
                </code>
                <Button variant="ghost" size="sm">
                  Copy
                </Button>
              </div>
            </SettingRow>
            <SettingRow
              label="Development API Key"
              description="Used for development and testing"
            >
              <Button variant="outline" size="sm">
                Generate
              </Button>
            </SettingRow>
          </div>
        </SettingsSection>

        {/* Notifications Section */}
        <SettingsSection
          title="Notifications"
          description="Configure how you receive updates"
          icon={Bell}
        >
          <div className="space-y-0">
            <SettingRow
              label="Email notifications"
              description="Receive updates via email"
            >
              <ToggleSwitch enabled={true} onChange={() => {}} />
            </SettingRow>
            <SettingRow
              label="Processing complete alerts"
              description="Get notified when tasks finish"
            >
              <ToggleSwitch enabled={true} onChange={() => {}} />
            </SettingRow>
            <SettingRow
              label="Weekly analytics digest"
              description="Summary of your usage and improvements"
            >
              <ToggleSwitch enabled={false} onChange={() => {}} />
            </SettingRow>
          </div>
        </SettingsSection>

        {/* Security Section */}
        <SettingsSection
          title="Security"
          description="Protect your account"
          icon={Shield}
        >
          <div className="space-y-0">
            <SettingRow
              label="Two-factor authentication"
              description="Add an extra layer of security"
            >
              <Button variant="outline" size="sm">
                Enable
              </Button>
            </SettingRow>
            <SettingRow label="Active sessions" description="Manage your logged-in devices">
              <Button variant="ghost" size="sm">
                View all
              </Button>
            </SettingRow>
          </div>
        </SettingsSection>

        {/* Help Section */}
        <SettingsSection
          title="Help & Support"
          description="Get help with Chakra"
          icon={HelpCircle}
        >
          <div className="flex gap-3">
            <Button variant="outline" size="sm">
              Documentation
            </Button>
            <Button variant="outline" size="sm">
              Contact Support
            </Button>
          </div>
        </SettingsSection>
      </div>
    </div>
  );
}
