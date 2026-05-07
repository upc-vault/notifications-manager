//
//  ViewController.swift
//  Omega Push Notifications Test
//
//  Main view controller with FCM token display and copy functionality
//

import UIKit

class ViewController: UIViewController {
    
    // MARK: - UI Elements
    
    private let scrollView: UIScrollView = {
        let scroll = UIScrollView()
        scroll.translatesAutoresizingMaskIntoConstraints = false
        return scroll
    }()
    
    private let contentView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private let logoLabel: UILabel = {
        let label = UILabel()
        label.text = "Ω"
        label.font = .systemFont(ofSize: 80, weight: .bold)
        label.textAlignment = .center
        label.textColor = .systemPurple
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let titleLabel: UILabel = {
        let label = UILabel()
        label.text = "Omega Push Notifications"
        label.font = .systemFont(ofSize: 24, weight: .bold)
        label.textAlignment = .center
        label.textColor = .label
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let subtitleLabel: UILabel = {
        let label = UILabel()
        label.text = "Firebase Cloud Messaging Test"
        label.font = .systemFont(ofSize: 16, weight: .regular)
        label.textAlignment = .center
        label.textColor = .secondaryLabel
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let statusLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .center
        label.font = .systemFont(ofSize: 18, weight: .semibold)
        label.textColor = .secondaryLabel
        label.text = "🔄 Initializing..."
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let tokenContainerView: UIView = {
        let view = UIView()
        view.backgroundColor = .secondarySystemBackground
        view.layer.cornerRadius = 12
        view.layer.borderWidth = 2
        view.layer.borderColor = UIColor.systemGray4.cgColor
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private let tokenTitleLabel: UILabel = {
        let label = UILabel()
        label.text = "FCM Token"
        label.font = .systemFont(ofSize: 14, weight: .semibold)
        label.textColor = .secondaryLabel
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let tokenLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .left
        label.font = .monospacedSystemFont(ofSize: 12, weight: .regular)
        label.textColor = .label
        label.text = "Waiting for token..."
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let copyButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("📋 Copy Token", for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 18, weight: .semibold)
        button.backgroundColor = .systemPurple
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 12
        button.translatesAutoresizingMaskIntoConstraints = false
        return button
    }()
    
    private let instructionsLabel: UILabel = {
        let label = UILabel()
        label.numberOfLines = 0
        label.textAlignment = .center
        label.font = .systemFont(ofSize: 14)
        label.textColor = .secondaryLabel
        label.text = """
        Instructions:
        1. Copy your FCM token above
        2. Go to http://localhost:5000/test/push
        3. Paste token and send test notification
        4. Check your device for the notification!
        """
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let notificationHistoryLabel: UILabel = {
        let label = UILabel()
        label.text = "Recent Notifications"
        label.font = .systemFont(ofSize: 18, weight: .bold)
        label.textColor = .label
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()
    
    private let historyTextView: UITextView = {
        let textView = UITextView()
        textView.backgroundColor = .secondarySystemBackground
        textView.font = .monospacedSystemFont(ofSize: 11, weight: .regular)
        textView.textColor = .label
        textView.layer.cornerRadius = 12
        textView.isEditable = false
        textView.text = "No notifications received yet..."
        textView.translatesAutoresizingMaskIntoConstraints = false
        return textView
    }()
    
    // MARK: - Properties
    
    private var currentToken: String?
    private var notificationHistory: [String] = []

    // MARK: - Lifecycle
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
        setupObservers()
        checkForToken()
    }
    
    // MARK: - Setup
    
    private func setupUI() {
        view.backgroundColor = .systemBackground
        
        // Add scroll view
        view.addSubview(scrollView)
        scrollView.addSubview(contentView)
        
        // Add all subviews to content view
        contentView.addSubview(logoLabel)
        contentView.addSubview(titleLabel)
        contentView.addSubview(subtitleLabel)
        contentView.addSubview(statusLabel)
        contentView.addSubview(tokenContainerView)
        tokenContainerView.addSubview(tokenTitleLabel)
        tokenContainerView.addSubview(tokenLabel)
        contentView.addSubview(copyButton)
        contentView.addSubview(instructionsLabel)
        contentView.addSubview(notificationHistoryLabel)
        contentView.addSubview(historyTextView)
        
        // Layout constraints
        NSLayoutConstraint.activate([
            // Scroll view
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
            
            // Content view
            contentView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),
            contentView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
            
            // Logo
            logoLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            logoLabel.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            
            // Title
            titleLabel.topAnchor.constraint(equalTo: logoLabel.bottomAnchor, constant: 8),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            titleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // Subtitle
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 4),
            subtitleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            subtitleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // Status
            statusLabel.topAnchor.constraint(equalTo: subtitleLabel.bottomAnchor, constant: 20),
            statusLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            statusLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // Token container
            tokenContainerView.topAnchor.constraint(equalTo: statusLabel.bottomAnchor, constant: 20),
            tokenContainerView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            tokenContainerView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // Token title
            tokenTitleLabel.topAnchor.constraint(equalTo: tokenContainerView.topAnchor, constant: 12),
            tokenTitleLabel.leadingAnchor.constraint(equalTo: tokenContainerView.leadingAnchor, constant: 12),
            tokenTitleLabel.trailingAnchor.constraint(equalTo: tokenContainerView.trailingAnchor, constant: -12),
            
            // Token label
            tokenLabel.topAnchor.constraint(equalTo: tokenTitleLabel.bottomAnchor, constant: 8),
            tokenLabel.leadingAnchor.constraint(equalTo: tokenContainerView.leadingAnchor, constant: 12),
            tokenLabel.trailingAnchor.constraint(equalTo: tokenContainerView.trailingAnchor, constant: -12),
            tokenLabel.bottomAnchor.constraint(equalTo: tokenContainerView.bottomAnchor, constant: -12),
            
            // Copy button
            copyButton.topAnchor.constraint(equalTo: tokenContainerView.bottomAnchor, constant: 16),
            copyButton.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            copyButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            copyButton.heightAnchor.constraint(equalToConstant: 50),
            
            // Instructions
            instructionsLabel.topAnchor.constraint(equalTo: copyButton.bottomAnchor, constant: 20),
            instructionsLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            instructionsLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // History title
            notificationHistoryLabel.topAnchor.constraint(equalTo: instructionsLabel.bottomAnchor, constant: 30),
            notificationHistoryLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            notificationHistoryLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            
            // History text view
            historyTextView.topAnchor.constraint(equalTo: notificationHistoryLabel.bottomAnchor, constant: 12),
            historyTextView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 20),
            historyTextView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -20),
            historyTextView.heightAnchor.constraint(equalToConstant: 150),
            historyTextView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -20)
        ])
        
        // Add button action
        copyButton.addTarget(self, action: #selector(copyTokenTapped), for: .touchUpInside)
        copyButton.isEnabled = false
    }
    
    private func setupObservers() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(tokenReceived(_:)),
            name: .fcmTokenReceived,
            object: nil
        )
    }
    
    private func checkForToken() {
        if let token = UserDefaults.standard.string(forKey: "fcmToken") {
            updateUI(with: token)
        }
    }
    
    // MARK: - Actions
    
    @objc private func tokenReceived(_ notification: Notification) {
        if let token = notification.object as? String {
            DispatchQueue.main.async {
                self.updateUI(with: token)
            }
        }
    }
    
    private func updateUI(with token: String) {
        currentToken = token
        
        // Update token label
        tokenLabel.text = token
        
        // Update status
        statusLabel.text = "✅ Ready to receive notifications!"
        statusLabel.textColor = .systemGreen
        
        // Enable copy button
        copyButton.isEnabled = true
        
        // Update border color
        tokenContainerView.layer.borderColor = UIColor.systemGreen.cgColor
        
        print("Token available in UI: \(token)")
    }
    
    @objc private func copyTokenTapped() {
        guard let token = currentToken else { return }
        
        // Copy to clipboard
        UIPasteboard.general.string = token
        
        // Show alert
        let alert = UIAlertController(
            title: "✅ Token Copied!",
            message: "Your FCM token has been copied to clipboard.\n\nNow paste it in the web interface at:\nhttp://localhost:5000/test/push",
            preferredStyle: .alert
        )
        
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
        
        // Visual feedback on button
        copyButton.setTitle("✓ Copied!", for: .normal)
        copyButton.backgroundColor = .systemGreen
        
        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
            self.copyButton.setTitle("📋 Copy Token", for: .normal)
            self.copyButton.backgroundColor = .systemPurple
        }
    }
    
    // MARK: - Public Methods
    
    func addNotificationToHistory(title: String, body: String, data: [AnyHashable: Any]?) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        var entry = "[\(timestamp)] \(title): \(body)"
        
        if let data = data, !data.isEmpty {
            entry += "\nData: \(data)"
        }
        
        notificationHistory.insert(entry, at: 0)
        
        // Keep only last 10 notifications
        if notificationHistory.count > 10 {
            notificationHistory.removeLast()
        }
        
        // Update text view
        DispatchQueue.main.async {
            self.historyTextView.text = self.notificationHistory.joined(separator: "\n\n---\n\n")
        }
    }
    
    // MARK: - Cleanup
    
    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
