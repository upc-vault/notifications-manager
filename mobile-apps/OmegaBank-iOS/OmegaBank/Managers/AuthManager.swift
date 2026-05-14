import SwiftUI

class AuthManager: ObservableObject {
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    
    init() {
        checkAuthStatus()
    }
    
    func checkAuthStatus() {
        if let token = UserDefaults.standard.string(forKey: "access_token"),
           !token.isEmpty {
            isAuthenticated = true
            loadUserData()
        }
    }
    
    func login(username: String, password: String, completion: @escaping (Result<Void, Error>) -> Void) {
        APIService.shared.login(username: username, password: password) { [weak self] result in
            switch result {
            case .success(let response):
                self?.saveAuthData(response)
                self?.isAuthenticated = true
                completion(.success(()))
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }
    
    func register(username: String, email: String, password: String, fullName: String, completion: @escaping (Result<Void, Error>) -> Void) {
        APIService.shared.register(username: username, email: email, password: password, fullName: fullName) { [weak self] result in
            switch result {
            case .success(let response):
                self?.saveAuthData(response)
                self?.isAuthenticated = true
                completion(.success(()))
            case .failure(let error):
                completion(.failure(error))
            }
        }
    }
    
    func logout() {
        UserDefaults.standard.removeObject(forKey: "access_token")
        UserDefaults.standard.removeObject(forKey: "refresh_token")
        UserDefaults.standard.removeObject(forKey: "user_data")
        isAuthenticated = false
        currentUser = nil
    }
    
    private func saveAuthData(_ response: LoginResponse) {
        UserDefaults.standard.set(response.accessToken, forKey: "access_token")
        UserDefaults.standard.set(response.refreshToken, forKey: "refresh_token")
        
        if let encoded = try? JSONEncoder().encode(response.user) {
            UserDefaults.standard.set(encoded, forKey: "user_data")
        }
        
        currentUser = response.user
    }
    
    private func loadUserData() {
        if let data = UserDefaults.standard.data(forKey: "user_data"),
           let user = try? JSONDecoder().decode(User.self, from: data) {
            currentUser = user
        }
    }
}
