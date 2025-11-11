import 'package:flutter/material.dart';
import 'pages/home_page.dart';

void main() {
  runApp(const CeasaApp());
}

class CeasaApp extends StatelessWidget {
  const CeasaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Ceasa App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primarySwatch: Colors.green,
      ),
      home: const HomePage(),
    );
  }
}
