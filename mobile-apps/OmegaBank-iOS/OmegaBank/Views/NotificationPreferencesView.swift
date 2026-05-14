import SwiftUI

struct NotificationPreferencesView: View {
    @State private var pushEnabled = true
    @State private var emailEnabled = true
    @State private var smsEnabled = true
    @State private var whatsappEnabled = true
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    var body: some View {
        Form {
            Section(header: Text("Notification Channels")) {
                Toggle("Push Notifications", isOn: $pushEnabled)
                    .onChange(of: pushEnabled) { newValue in
                        updatePreference(key: "push_enabled", value: newValue)
                    }
                
                Toggle("Email Notifications", isOn: $emailEnabled)
                    .onChange(of: emailEnabled) { newValue in
                        updatePreference(key: "email_enabled", value: newValue)
                    }
                
                Toggle("SMS Notifications", isOn: $smsEnabled)
                    .onChange(of: smsEnabled) { newValue in
                        updatePreference(key: "sms_enabled", value: newValue)
                    }
                
                Toggle("WhatsApp Notifications", isOn: $whatsappEnabled)
                    .onChange(of: whatsappEnabled) { newValue in
                        updatePreference(key: "whatsapp_enabled", value: newValue)
                    }
            }
            
            Section(footer: Text("When disabled, you won't receive notifications through that channel.")) {
                EmptyView()
            }
            
            if let error = errorMessage {
                Section {
                    Text(error)
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }
        }
        .navigationTitle("Notification Settings")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear(perform: loadPreferences)
        .overlay {
            if isLoading {
                ProgressView()
            }
        }
    }
    
    private func loadPreferences() {
        isLoading = true
        
        APIService.shared.getPreferences { result in
            isLoading = false
            switch result {
            case .success(let response):
                if let channels = response.channels {
                    pushEnabled = channels["push"] ?? true
                    emailEnabled = channels["email"] ?? true
                    smsEnabled = channels["sms"] ?? true
                    whatsappEnabled = channels["whatsapp"] ?? true
                }
            case .failure(let error):
                errorMessage = error.localizedDescription
            }
        }
    }
    
    private func updatePreference(key: String, value: Bool) {
        let params: [String: Any] = [key: value]
        
        APIService.shared.updatePreferences(parameters: params) { result in
            switch result {
            case .success(_):
                print("✓ Preference updated: \(key) = \(value)")
            case .failure(let error):
                errorMessage = error.localizedDescription
                // Revert the toggle
                loadPreferences()
            }
        }
    }
}

#Preview {
    NavigationView {
        NotificationPreferencesView()
    }
}
