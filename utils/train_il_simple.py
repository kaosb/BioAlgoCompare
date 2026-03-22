#!/usr/bin/env python3
"""
Simple IL Training without PyTorch
==================================

Trains a simple IL model using sklearn instead of PyTorch to avoid
compatibility issues.
"""

import argparse
import json
import numpy as np
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score


class SimpleILModel:
    """Simple IL model using Random Forest."""
    
    def __init__(self, n_estimators=100, random_state=42):
        """Initialize the model."""
        self.scaler = StandardScaler()
        self.models = {
            'alpha': RandomForestRegressor(n_estimators=n_estimators, random_state=random_state),
            'beta': RandomForestRegressor(n_estimators=n_estimators, random_state=random_state),
            'gamma': RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
        }
        self.feature_names = None
        self.is_trained = False
        
    def prepare_features(self, df):
        """Prepare features from dataframe."""
        # Select state features (exclude target and metadata columns)
        exclude_cols = ['instance', 'algorithm', 'demo_id', 'alpha', 'beta', 'gamma', 
                       'improvement', 'fitness_after']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        self.feature_names = feature_cols
        return df[feature_cols].values
    
    def train(self, df_train, df_val=None):
        """Train the model."""
        # Prepare features
        X_train = self.prepare_features(df_train)
        X_train = self.scaler.fit_transform(X_train)
        
        # Train each model
        results = {}
        for param in ['alpha', 'beta', 'gamma']:
            y_train = df_train[param].values
            
            # Train
            self.models[param].fit(X_train, y_train)
            
            # Evaluate on training set
            train_pred = self.models[param].predict(X_train)
            train_mse = mean_squared_error(y_train, train_pred)
            train_r2 = r2_score(y_train, train_pred)
            
            results[param] = {
                'train_mse': train_mse,
                'train_r2': train_r2,
                'feature_importance': dict(zip(self.feature_names, 
                                             self.models[param].feature_importances_))
            }
            
            # Validation if provided
            if df_val is not None:
                X_val = self.prepare_features(df_val)
                X_val = self.scaler.transform(X_val)
                y_val = df_val[param].values
                
                val_pred = self.models[param].predict(X_val)
                results[param]['val_mse'] = mean_squared_error(y_val, val_pred)
                results[param]['val_r2'] = r2_score(y_val, val_pred)
        
        self.is_trained = True
        return results
    
    def predict(self, state_dict):
        """Predict parameters for a given state."""
        if not self.is_trained:
            return 0.5, 0.5, 0.65  # Default values
        
        # Convert state dict to feature array
        features = np.array([state_dict.get(fname, 0) for fname in self.feature_names])
        features = features.reshape(1, -1)
        features = self.scaler.transform(features)
        
        # Predict
        alpha = self.models['alpha'].predict(features)[0]
        beta = self.models['beta'].predict(features)[0]
        gamma = self.models['gamma'].predict(features)[0]
        
        # Clip to valid ranges
        alpha = np.clip(alpha, 0.1, 0.9)
        beta = np.clip(beta, 0.2, 0.8)
        gamma = np.clip(gamma, 0.3, 1.0)
        
        return alpha, beta, gamma
    
    def save(self, filepath):
        """Save the model."""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'models': self.models,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'is_trained': self.is_trained
            }, f)
        print(f"Model saved to {filepath}")
    
    def load(self, filepath):
        """Load the model."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.models = data['models']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            self.is_trained = data['is_trained']
        # Suppress repeated load messages in batch experiments


def analyze_training_results(results, df_train, df_val=None):
    """Analyze and print training results."""
    print("\n📊 Training Results:")
    print("="*50)
    
    for param in ['alpha', 'beta', 'gamma']:
        print(f"\n{param.upper()}:")
        print(f"  Train MSE: {results[param]['train_mse']:.6f}")
        print(f"  Train R²:  {results[param]['train_r2']:.4f}")
        
        if 'val_mse' in results[param]:
            print(f"  Val MSE:   {results[param]['val_mse']:.6f}")
            print(f"  Val R²:    {results[param]['val_r2']:.4f}")
        
        # Top 5 features
        importance = results[param]['feature_importance']
        top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
        print("  Top features:")
        for feat, imp in top_features:
            print(f"    - {feat}: {imp:.4f}")
    
    # Dataset statistics
    print("\n📈 Dataset Statistics:")
    print(f"  Training samples: {len(df_train)}")
    if df_val is not None:
        print(f"  Validation samples: {len(df_val)}")
    
    print("\n  Parameter ranges in training data:")
    for param in ['alpha', 'beta', 'gamma']:
        print(f"    {param}: [{df_train[param].min():.3f}, {df_train[param].max():.3f}]")


def main():
    parser = argparse.ArgumentParser(description='Train IL model for HO')
    parser.add_argument('--demos', type=str, default='data/demos/ho_demos.csv',
                       help='Path to demonstrations CSV')
    parser.add_argument('--output', type=str, default='models/ho_il_model.pkl',
                       help='Output model path')
    parser.add_argument('--test_split', type=float, default=0.2,
                       help='Validation split ratio')
    parser.add_argument('--n_estimators', type=int, default=100,
                       help='Number of trees in Random Forest')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    
    args = parser.parse_args()
    
    print("🚀 Training IL Model")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load demonstrations
    print(f"\n📁 Loading demonstrations from {args.demos}")
    df = pd.read_csv(args.demos)
    print(f"   Loaded {len(df)} demonstrations")
    
    # Split data
    df_train, df_val = train_test_split(df, test_size=args.test_split, 
                                        random_state=args.seed)
    
    # Create and train model
    print("\n🔧 Training Random Forest models...")
    model = SimpleILModel(n_estimators=args.n_estimators, random_state=args.seed)
    results = model.train(df_train, df_val)
    
    # Analyze results
    analyze_training_results(results, df_train, df_val)
    
    # Save model
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(output_path)
    
    # Save training report
    report_path = output_path.with_suffix('.json')
    with open(report_path, 'w') as f:
        json.dump({
            'training_date': datetime.now().isoformat(),
            'n_train': len(df_train),
            'n_val': len(df_val),
            'results': results,
            'args': vars(args)
        }, f, indent=2)
    
    print("\n✅ Training complete!")
    print(f"   Model saved to: {output_path}")
    print(f"   Report saved to: {report_path}")
    print(f"   Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()