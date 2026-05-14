import Foundation

class APIService {
    static let shared = APIService()
    
    private let baseURL = "http://localhost:8080/api/v1"
    private var accessToken: String? {
        get { UserDefaults.standard.string(forKey: "access_token") }
        set { UserDefaults.standard.set(newValue, forKey: "access_token") }
    }
    
    private init() {}
    
    // MARK: - Auth
    
    func login(username: String, password: String, completion: @escaping (Result<LoginResponse, Error>) -> Void) {
        let parameters = ["username": username, "password": password]
        request(endpoint: "/auth/login", method: "POST", parameters: parameters, completion: completion)
    }
    
    func register(username: String, email: String, password: String, fullName: String, completion: @escaping (Result<LoginResponse, Error>) -> Void) {
        let parameters = [
            "username": username,
            "email": email,
            "password": password,
            "full_name": fullName
        ]
        request(endpoint: "/auth/register", method: "POST", parameters: parameters, completion: completion)
    }
    
    // MARK: - Push Notifications
    
    func registerPushToken(parameters: [String: Any], completion: @escaping (Result<PushRegisterResponse, Error>) -> Void) {
        request(endpoint: "/push/register", method: "POST", parameters: parameters, requiresAuth: true, completion: completion)
    }
    
    // MARK: - Transfers
    
    func createTransfer(receiverUsername: String, amount: Double, description: String?, completion: @escaping (Result<TransferResponse, Error>) -> Void) {
        var parameters: [String: Any] = [
            "receiver_username": receiverUsername,
            "amount": amount
        ]
        if let desc = description {
            parameters["description"] = desc
        }
        request(endpoint: "/transfers", method: "POST", parameters: parameters, requiresAuth: true, completion: completion)
    }
    
    func getTransfers(type: String = "all", limit: Int = 50, offset: Int = 0, completion: @escaping (Result<TransfersListResponse, Error>) -> Void) {
        let endpoint = "/transfers?type=\(type)&limit=\(limit)&offset=\(offset)"
        request(endpoint: endpoint, method: "GET", requiresAuth: true, completion: completion)
    }
    
    // MARK: - Preferences
    
    func getPreferences(completion: @escaping (Result<PreferencesResponse, Error>) -> Void) {
        request(endpoint: "/preferences", method: "GET", requiresAuth: true, completion: completion)
    }
    
    func updatePreferences(parameters: [String: Any], completion: @escaping (Result<PreferencesResponse, Error>) -> Void) {
        request(endpoint: "/preferences", method: "PUT", parameters: parameters, requiresAuth: true, completion: completion)
    }
    
    // MARK: - Generic Request
    
    private func request<T: Decodable>(
        endpoint: String,
        method: String,
        parameters: [String: Any]? = nil,
        requiresAuth: Bool = false,
        completion: @escaping (Result<T, Error>) -> Void
    ) {
        guard let url = URL(string: baseURL + endpoint) else {
            completion(.failure(NSError(domain: "", code: -1, userInfo: [NSLocalizedDescriptionKey: "Invalid URL"])))
            return
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        if requiresAuth, let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        
        if let parameters = parameters {
            request.httpBody = try? JSONSerialization.data(withJSONObject: parameters)
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(error))
                }
                return
            }
            
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(NSError(domain: "", code: -1, userInfo: [NSLocalizedDescriptionKey: "No data"])))
                }
                return
            }
            
            do {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                let result = try decoder.decode(T.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                // Try to parse error message
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let errorMessage = json["error"] as? String {
                    DispatchQueue.main.async {
                        completion(.failure(NSError(domain: "", code: -1, userInfo: [NSLocalizedDescriptionKey: errorMessage])))
                    }
                } else {
                    DispatchQueue.main.async {
                        completion(.failure(error))
                    }
                }
            }
        }.resume()
    }
}

// MARK: - Response Models

struct LoginResponse: Codable {
    let message: String
    let accessToken: String
    let refreshToken: String
    let user: User
}

struct User: Codable {
    let id: Int
    let username: String
    let email: String
    let fullName: String?
}

struct PushRegisterResponse: Codable {
    let status: String
    let message: String
    let username: String
    let platform: String
}

struct Transfer: Codable, Identifiable {
    let id: Int
    let senderId: Int
    let receiverId: Int
    let amount: Double
    let currency: String
    let status: String
    let description: String?
    let referenceNumber: String
    let notificationSent: Bool
    let createdAt: String
    let completedAt: String?
}

struct TransferResponse: Codable {
    let success: Bool
    let message: String
    let transfer: Transfer
}

struct TransfersListResponse: Codable {
    let success: Bool
    let total: Int
    let limit: Int
    let offset: Int
    let transfers: [Transfer]
}

struct PreferencesResponse: Codable {
    let userId: Int
    let quietHours: [String: Any]?
    let channels: [String: Bool]?
    let notificationTypes: [String: Bool]?
    
    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case quietHours = "quiet_hours"
        case channels
        case notificationTypes = "notification_types"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        userId = try container.decode(Int.self, forKey: .userId)
        
        // Decode optional dictionaries
        if let channelsDict = try? container.decode([String: Bool].self, forKey: .channels) {
            channels = channelsDict
        } else {
            channels = nil
        }
        
        quietHours = nil
        notificationTypes = nil
    }
}
