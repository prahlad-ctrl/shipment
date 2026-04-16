import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyD3Rrq9KTtPEy8jjHA2lAqPXd1m2J08yPM",
  authDomain: "deepfrog-df199.firebaseapp.com",
  projectId: "deepfrog-df199",
  storageBucket: "deepfrog-df199.firebasestorage.app",
  messagingSenderId: "429468574014",
  appId: "1:429468574014:web:e7a629d171a88c120b0c6f",
  measurementId: "G-D1YSFFS71Y"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
