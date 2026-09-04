import { Component } from '@angular/core';
import { Search } from './search/search';

@Component({
  imports: [Search],
  selector: 'app-home',
  styleUrl: './home.css',
  templateUrl: './home.html',
})
export class Home {}