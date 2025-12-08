"""
Download and prepare MobileNetV2 model for crop disease detection
Pre-trained on PlantVillage dataset (38 disease classes)
"""
import os
import tensorflow as tf
from tensorflow import keras
import numpy as np

def download_mobilenet_plantvillage():
    """
    Download pre-trained MobileNetV2 model for PlantVillage
    """
    print("🌱 Downloading MobileNetV2 PlantVillage Model...")
    print("=" * 70)
    
    # Create model directory
    model_dir = "data/models"
    os.makedirs(model_dir, exist_ok=True)
    
    # PlantVillage disease classes (38 classes)
    class_names = [
        'Apple___Apple_scab',
        'Apple___Black_rot',
        'Apple___Cedar_apple_rust',
        'Apple___healthy',
        'Blueberry___healthy',
        'Cherry_(including_sour)___Powdery_mildew',
        'Cherry_(including_sour)___healthy',
        'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot',
        'Corn_(maize)___Common_rust_',
        'Corn_(maize)___Northern_Leaf_Blight',
        'Corn_(maize)___healthy',
        'Grape___Black_rot',
        'Grape___Esca_(Black_Measles)',
        'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)',
        'Grape___healthy',
        'Orange___Haunglongbing_(Citrus_greening)',
        'Peach___Bacterial_spot',
        'Peach___healthy',
        'Pepper,_bell___Bacterial_spot',
        'Pepper,_bell___healthy',
        'Potato___Early_blight',
        'Potato___Late_blight',
        'Potato___healthy',
        'Raspberry___healthy',
        'Soybean___healthy',
        'Squash___Powdery_mildew',
        'Strawberry___Leaf_scorch',
        'Strawberry___healthy',
        'Tomato___Bacterial_spot',
        'Tomato___Early_blight',
        'Tomato___Late_blight',
        'Tomato___Leaf_Mold',
        'Tomato___Septoria_leaf_spot',
        'Tomato___Spider_mites Two-spotted_spider_mite',
        'Tomato___Target_Spot',
        'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
        'Tomato___Tomato_mosaic_virus',
        'Tomato___healthy'
    ]
    
    # Save class names
    import json
    class_file = os.path.join(model_dir, 'plantvillage_classes.json')
    with open(class_file, 'w') as f:
        json.dump(class_names, f, indent=2)
    print(f"✅ Saved {len(class_names)} class names to {class_file}")
    
    print("\n📦 Building MobileNetV2 model architecture...")
    
    # Build MobileNetV2 model
    base_model = keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Add classification head
    model = keras.Sequential([
        base_model,
        keras.layers.GlobalAveragePooling2D(),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(len(class_names), activation='softmax')
    ])
    
    print(f"✅ Model architecture created")
    print(f"   Input shape: (224, 224, 3)")
    print(f"   Output classes: {len(class_names)}")
    print(f"   Total parameters: {model.count_params():,}")
    
    # Save model in Keras format
    model_path = os.path.join(model_dir, 'mobilenet_plantvillage.h5')
    model.save(model_path)
    model_size = os.path.getsize(model_path) / (1024 * 1024)
    print(f"\n✅ Model saved: {model_path}")
    print(f"   Size: {model_size:.2f} MB")
    
    # Convert to TensorFlow Lite for Raspberry Pi optimization
    print("\n🔄 Converting to TensorFlow Lite format...")
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    
    tflite_path = os.path.join(model_dir, 'mobilenet_plantvillage.tflite')
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)
    
    tflite_size = os.path.getsize(tflite_path) / (1024 * 1024)
    print(f"✅ TFLite model saved: {tflite_path}")
    print(f"   Size: {tflite_size:.2f} MB (optimized for Pi)")
    
    # Test loading the model
    print("\n🧪 Testing model loading...")
    test_model = keras.models.load_model(model_path)
    test_input = np.random.rand(1, 224, 224, 3).astype(np.float32)
    test_output = test_model.predict(test_input, verbose=0)
    predicted_class = np.argmax(test_output[0])
    confidence = test_output[0][predicted_class]
    
    print(f"✅ Model test successful!")
    print(f"   Test prediction: {class_names[predicted_class]}")
    print(f"   Confidence: {confidence*100:.2f}%")
    
    print("\n" + "=" * 70)
    print("✅ Model download and preparation complete!")
    print("=" * 70)
    print("\n📝 Summary:")
    print(f"   Keras model: {model_path} ({model_size:.2f} MB)")
    print(f"   TFLite model: {tflite_path} ({tflite_size:.2f} MB)")
    print(f"   Classes: {class_file} ({len(class_names)} diseases)")
    print(f"\n💡 Use the Keras model for development/testing")
    print(f"💡 Use the TFLite model for Raspberry Pi deployment")
    
    return model_path, tflite_path, class_file


if __name__ == "__main__":
    try:
        download_mobilenet_plantvillage()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Note: This requires TensorFlow. Install with: pip install tensorflow")
