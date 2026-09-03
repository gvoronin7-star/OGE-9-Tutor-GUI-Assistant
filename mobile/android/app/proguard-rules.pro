# ONNX Runtime resolves Java classes such as ai.onnxruntime.TensorInfo from
# native code via JNI at inference time (ai.onnxruntime.OrtSession.run()).
# R8 cannot see that link statically and strips/renames the classes, which
# crashes release builds with ClassNotFoundException - see
# decisions/2026-09-02 entry in decision-log.md ("Найден краш поиска в
# релизной сборке").
-keep class ai.onnxruntime.** { *; }
-dontwarn ai.onnxruntime.**
